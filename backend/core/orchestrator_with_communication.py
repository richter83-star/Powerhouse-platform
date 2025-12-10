"""
Orchestrator with integrated communication protocol for true multi-agent collaboration.
"""

from typing import List, Dict, Any, Optional
from importlib import import_module
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import uuid

from core.orchestrator import Orchestrator
from core.agent_communication_helper import AgentCommunicationHelper, enable_agent_communication
from communication import CommunicationProtocol, MessageType
from utils.logging import get_logger

logger = get_logger(__name__)


class OrchestratorWithCommunication(Orchestrator):
    """
    Enhanced orchestrator with full communication protocol integration.
    
    Features:
    - Agents register with communication protocol
    - Agents can discover and communicate with each other
    - Shared context for collaborative work
    - Consensus mechanisms (voting, negotiation)
    - Agent delegation and task decomposition
    """
    
    def __init__(
        self,
        agent_names: List[str],
        max_agents: int = 19,
        execution_mode: str = "collaborative",  # New mode: collaborative
        enable_consensus: bool = True,
        protocol: Optional[CommunicationProtocol] = None
    ):
        """
        Initialize orchestrator with communication protocol.
        
        Args:
            agent_names: List of agent names to load
            max_agents: Maximum number of agents
            execution_mode: Execution mode
            enable_consensus: Enable consensus mechanisms
            protocol: Communication protocol instance (creates new if None)
        """
        super().__init__(agent_names, max_agents, execution_mode)
        
        # Initialize communication protocol
        self.protocol = protocol or CommunicationProtocol()
        self.enable_consensus = enable_consensus
        
        # Register all agents with protocol
        self._register_agents_with_protocol()
        
        # Track active collaborations
        self.active_collaborations: Dict[str, Dict[str, Any]] = {}
        
        # Communication helpers for agents
        self.communication_helpers: Dict[str, AgentCommunicationHelper] = {}
        
        logger.info(
            f"OrchestratorWithCommunication initialized with {len(self.agents)} agents, "
            f"communication protocol enabled"
        )
    
    def _register_agents_with_protocol(self):
        """Register all agents with the communication protocol."""
        for agent in self.agents:
            try:
                # Get agent metadata
                agent_name = agent.__class__.__name__
                agent_type = agent_name.replace("Agent", "").lower()
                
                # Try to get capabilities from agent
                capabilities = getattr(agent, "capabilities", [])
                if not capabilities:
                    # Infer capabilities from agent type
                    capabilities = self._infer_capabilities(agent_type)
                
                # Register with protocol
                self.protocol.register_agent(
                    name=agent_name,
                    agent_type=agent_type,
                    capabilities=capabilities,
                    metadata={
                        "orchestrator_managed": True,
                        "registered_at": datetime.now().isoformat()
                    }
                )
                
                # Give agent access to protocol (if it supports it)
                if hasattr(agent, "protocol"):
                    agent.protocol = self.protocol
                if hasattr(agent, "register"):
                    try:
                        agent.register(self.protocol)
                    except:
                        pass  # Agent might not support BaseAgent protocol
                
                logger.debug(f"Registered agent {agent_name} with communication protocol")
                
            except Exception as e:
                logger.warning(f"Failed to register agent {agent.__class__.__name__}: {e}")
    
    def _infer_capabilities(self, agent_type: str) -> List[str]:
        """Infer capabilities from agent type."""
        capability_map = {
            "react": ["reasoning", "acting", "tool_usage"],
            "chain_of_thought": ["reasoning", "step_by_step"],
            "tree_of_thought": ["reasoning", "exploration", "backtracking"],
            "planning": ["planning", "scheduling"],
            "evaluator": ["evaluation", "scoring"],
            "memory": ["memory", "storage"],
            "governor": ["governance", "safety"],
            "reflection": ["reflection", "self_critique"],
            "debate": ["debate", "multi_perspective"],
            "multi_agent": ["coordination", "delegation"],
        }
        
        return capability_map.get(agent_type, [agent_type])
    
    def run(self, task: str, config: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """
        Run agents with collaborative communication.
        
        Args:
            task: Task description
            config: Optional configuration
            
        Returns:
            Execution results
        """
        config = config or {}
        execution_mode = config.get("execution_mode", self.execution_mode)
        
        if execution_mode == "collaborative":
            return self.run_collaborative(task, config)
        else:
            # Fall back to parent implementation, but with protocol available
            return super().run(task, config)
    
    def run_collaborative(
        self,
        task: str,
        config: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        """
        Run agents in collaborative mode with full communication.
        
        Agents can:
        - Discover and communicate with each other
        - Delegate subtasks
        - Reach consensus on decisions
        - Share context and state
        
        Args:
            task: Task description
            config: Optional configuration
            
        Returns:
            Execution results with collaboration metadata
        """
        config = config or {}
        run_id = str(uuid.uuid4())
        
        # Initialize shared context
        context = {
            "task": task,
            "outputs": [],
            "state": {},
            "run_id": run_id,
            "collaboration_mode": True
        }
        
        # Set task in shared context
        self.protocol.shared_context.set("task", task, namespace="global")
        self.protocol.shared_context.set("run_id", run_id, namespace="global")
        
        logger.info(f"Starting collaborative execution: task={task[:50]}..., run_id={run_id}")
        
        # Pre-flight check
        gov = self._find_agent_by_type("GovernorAgent")
        if gov:
            ok, msg = gov.preflight(task)
            if not ok:
                return {"error": f"Governor blocked task: {msg}", "run_id": run_id}
        
        # Broadcast task start
        self.protocol.broadcast(
            sender="orchestrator",
            message_type=MessageType.NOTIFICATION,
            content={
                "event": "task_started",
                "task": task,
                "run_id": run_id
            },
            run_id=run_id
        )
        
        # Initialize collaboration session
        collaboration_id = str(uuid.uuid4())
        self.active_collaborations[collaboration_id] = {
            "run_id": run_id,
            "task": task,
            "started_at": datetime.now(),
            "agents_involved": [],
            "messages_exchanged": 0,
            "delegations": []
        }
        
        # Select agents for task (could use neural model here)
        selected_agents = self._select_agents_for_task(task, context)
        
        logger.info(f"Selected {len(selected_agents)} agents for collaborative execution")
        
        # Execute agents with communication
        for agent in selected_agents:
            agent_name = agent.__class__.__name__
            self.active_collaborations[collaboration_id]["agents_involved"].append(agent_name)
            
            try:
                # Check for messages from other agents
                messages = self.protocol.get_messages(agent_name)
                if messages:
                    logger.debug(f"Agent {agent_name} received {len(messages)} messages")
                    context["messages"] = [msg.to_dict() for msg in messages]
                    self.active_collaborations[collaboration_id]["messages_exchanged"] += len(messages)
                
                # Update agent status
                self.protocol.update_agent_status(agent_name, "busy")
                
                # Execute agent with communication support
                # Wrap agent if it doesn't have native communication
                if not hasattr(agent, "protocol") or agent.protocol is None:
                    comm_helper = self._get_communication_helper(agent, agent_name)
                    out = comm_helper.run_with_communication(context)
                else:
                    out = agent.run(context)
                
                # Store output in shared context
                output_key = f"{agent_name}_output"
                self.protocol.shared_context.set(output_key, out, namespace="global")
                
                context["outputs"].append({
                    "agent": agent_name,
                    "output": out,
                    "status": "success"
                })
                
                # Broadcast completion
                self.protocol.broadcast(
                    sender=agent_name,
                    message_type=MessageType.NOTIFICATION,
                    content={
                        "event": "agent_completed",
                        "agent": agent_name,
                        "output_key": output_key
                    },
                    run_id=run_id
                )
                
                # Check if agent wants to delegate
                if isinstance(out, dict) and out.get("delegate_to"):
                    delegation = self._handle_delegation(
                        agent_name,
                        out["delegate_to"],
                        out.get("delegation_task", task),
                        context,
                        run_id
                    )
                    if delegation:
                        self.active_collaborations[collaboration_id]["delegations"].append(delegation)
                
                self.protocol.update_agent_status(agent_name, "idle")
                
            except Exception as e:
                logger.error(f"Agent {agent_name} failed: {e}", exc_info=True)
                self.protocol.update_agent_status(agent_name, "error")
                context["outputs"].append({
                    "agent": agent_name,
                    "output": None,
                    "status": "error",
                    "error": str(e)
                })
        
        # Check for consensus if enabled
        if self.enable_consensus and config.get("require_consensus", False):
            consensus_result = self._reach_consensus(context, selected_agents, run_id)
            context["consensus"] = consensus_result
        
        # Post-processing
        evalr = self._find_agent_by_type("EvaluatorAgent")
        if evalr:
            context["evaluation"] = evalr.evaluate(context)
        
        # Broadcast task completion
        self.protocol.broadcast(
            sender="orchestrator",
            message_type=MessageType.NOTIFICATION,
            content={
                "event": "task_completed",
                "run_id": run_id,
                "outputs_count": len(context["outputs"])
            },
            run_id=run_id
        )
        
        # Finalize collaboration
        collaboration = self.active_collaborations[collaboration_id]
        collaboration["completed_at"] = datetime.now()
        collaboration["duration_seconds"] = (
            collaboration["completed_at"] - collaboration["started_at"]
        ).total_seconds()
        
        context["collaboration"] = collaboration
        
        logger.info(f"Collaborative execution completed: {collaboration['duration_seconds']:.2f}s")
        
        return context
    
    def _select_agents_for_task(self, task: str, context: Dict[str, Any]) -> List:
        """
        Select agents for task using capability matching.
        
        Args:
            task: Task description
            context: Execution context
            
        Returns:
            List of selected agents
        """
        # Simple selection based on task keywords
        # In production, use neural model or more sophisticated selection
        task_lower = task.lower()
        selected = []
        
        # Always include certain agents
        always_include = ["GovernorAgent", "AdaptiveMemoryAgent"]
        for agent in self.agents:
            if agent.__class__.__name__ in always_include:
                selected.append(agent)
        
        # Select based on task requirements
        if any(keyword in task_lower for keyword in ["reason", "think", "analyze"]):
            reasoning_agents = ["ReactAgent", "ChainOfThoughtAgent", "TreeOfThoughtAgent"]
            for agent in self.agents:
                if agent.__class__.__name__ in reasoning_agents and agent not in selected:
                    selected.append(agent)
                    break  # Add one reasoning agent
        
        if any(keyword in task_lower for keyword in ["plan", "schedule", "organize"]):
            for agent in self.agents:
                if "Planning" in agent.__class__.__name__ and agent not in selected:
                    selected.append(agent)
                    break
        
        # If no specific agents selected, use adaptive mode selection
        if len(selected) <= len(always_include):
            # Use capability-based discovery
            available_agents = self.protocol.find_by_capability("reasoning")
            if not available_agents:
                # Fallback: use all non-special agents
                for agent in self.agents:
                    if agent not in selected and not any(
                        skip in agent.__class__.__name__
                        for skip in ["Governor", "Evaluator", "MetaEvolver"]
                    ):
                        selected.append(agent)
                        if len(selected) >= 5:  # Limit selection
                            break
        
        return selected if selected else self.agents[:5]  # Fallback
    
    def _get_communication_helper(self, agent, agent_name: str) -> AgentCommunicationHelper:
        """Get or create communication helper for agent."""
        if agent_name not in self.communication_helpers:
            self.communication_helpers[agent_name] = enable_agent_communication(
                agent, agent_name, self.protocol
            )
        return self.communication_helpers[agent_name]
    
    def _find_agent_by_type(self, agent_type: str):
        """Find agent by class name."""
        for agent in self.agents:
            if agent.__class__.__name__ == agent_type:
                return agent
        return None
    
    def _handle_delegation(
        self,
        delegator: str,
        delegate_to: str,
        delegation_task: str,
        context: Dict[str, Any],
        run_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Handle task delegation between agents.
        
        Args:
            delegator: Agent delegating the task
            delegate_to: Agent or capability to delegate to
            delegation_task: Task to delegate
            context: Execution context
            run_id: Run ID
            
        Returns:
            Delegation result or None
        """
        logger.info(f"Handling delegation: {delegator} -> {delegate_to}")
        
        # Find delegate agent
        delegate_agent = None
        
        # Check if it's a capability
        available_agents = self.protocol.find_by_capability(delegate_to)
        if available_agents:
            # Select first available agent
            delegate_info = available_agents[0]
            delegate_agent = self._find_agent_by_name(delegate_info.name)
        else:
            # Check if it's an agent name
            delegate_agent = self._find_agent_by_name(delegate_to)
        
        if not delegate_agent:
            logger.warning(f"Could not find delegate: {delegate_to}")
            return None
        
        # Send delegation message
        message = self.protocol.send_message(
            sender=delegator,
            receiver=delegate_agent.__class__.__name__,
            message_type=MessageType.TASK_ASSIGNMENT,
            content={
                "task": delegation_task,
                "from_agent": delegator,
                "context": context
            },
            run_id=run_id
        )
        
        # Execute delegated task
        try:
            delegation_context = context.copy()
            delegation_context["task"] = delegation_task
            delegation_context["delegated_from"] = delegator
            
            result = delegate_agent.run(delegation_context)
            
            # Send result back
            self.protocol.send_message(
                sender=delegate_agent.__class__.__name__,
                receiver=delegator,
                message_type=MessageType.TASK_COMPLETE,
                content={
                    "task": delegation_task,
                    "result": result
                },
                run_id=run_id
            )
            
            return {
                "from": delegator,
                "to": delegate_agent.__class__.__name__,
                "task": delegation_task,
                "result": result,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Delegation failed: {e}", exc_info=True)
            return {
                "from": delegator,
                "to": delegate_to,
                "task": delegation_task,
                "status": "error",
                "error": str(e)
            }
    
    def _find_agent_by_name(self, name: str):
        """Find agent by name."""
        for agent in self.agents:
            if agent.__class__.__name__ == name:
                return agent
        return None
    
    def _reach_consensus(
        self,
        context: Dict[str, Any],
        agents: List,
        run_id: str
    ) -> Dict[str, Any]:
        """
        Reach consensus among agents using voting mechanism.
        
        Args:
            context: Execution context
            agents: List of agents to reach consensus
            run_id: Run ID
            
        Returns:
            Consensus result
        """
        logger.info(f"Reaching consensus among {len(agents)} agents")
        
        # Broadcast consensus proposal
        proposal_id = str(uuid.uuid4())
        proposal = {
            "proposal_id": proposal_id,
            "question": "Do you agree with the current solution?",
            "context": context
        }
        
        self.protocol.broadcast(
            sender="orchestrator",
            message_type=MessageType.PROPOSAL,
            content=proposal,
            run_id=run_id
        )
        
        # Collect votes
        votes = {}
        timeout = 30.0  # 30 second timeout
        start_time = datetime.now()
        
        for agent in agents:
            agent_name = agent.__class__.__name__
            
            # Check for vote message
            messages = self.protocol.get_messages(agent_name)
            for msg in messages:
                if (msg.message_type == MessageType.VOTE and
                    msg.content.get("proposal_id") == proposal_id):
                    votes[agent_name] = msg.content.get("vote", "abstain")
                    break
        
        # Simple majority vote
        yes_votes = sum(1 for v in votes.values() if v == "yes")
        no_votes = sum(1 for v in votes.values() if v == "no")
        total_votes = len(votes)
        
        consensus_reached = yes_votes > no_votes and total_votes >= len(agents) // 2
        
        result = {
            "proposal_id": proposal_id,
            "votes": votes,
            "yes_votes": yes_votes,
            "no_votes": no_votes,
            "total_votes": total_votes,
            "consensus_reached": consensus_reached,
            "majority": "yes" if yes_votes > no_votes else "no" if no_votes > yes_votes else "tie"
        }
        
        logger.info(f"Consensus result: {result['majority']} ({yes_votes}/{total_votes})")
        
        return result
    
    def get_collaboration_stats(self) -> Dict[str, Any]:
        """Get statistics about agent collaborations."""
        total_collaborations = len(self.active_collaborations)
        completed = sum(
            1 for c in self.active_collaborations.values()
            if "completed_at" in c
        )
        
        total_delegations = sum(
            len(c.get("delegations", []))
            for c in self.active_collaborations.values()
        )
        
        total_messages = sum(
            c.get("messages_exchanged", 0)
            for c in self.active_collaborations.values()
        )
        
        return {
            "total_collaborations": total_collaborations,
            "completed": completed,
            "active": total_collaborations - completed,
            "total_delegations": total_delegations,
            "total_messages_exchanged": total_messages,
            "protocol_stats": self.protocol.get_stats()
        }

