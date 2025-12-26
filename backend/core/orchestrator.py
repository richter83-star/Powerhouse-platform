from typing import List, Dict, Any, Optional
from importlib import import_module
import asyncio
from concurrent.futures import ThreadPoolExecutor
from utils.logging import get_logger

logger = get_logger(__name__)

# Import communication protocol (optional dependency)
try:
    from communication import CommunicationProtocol
    COMMUNICATION_AVAILABLE = True
except ImportError:
    COMMUNICATION_AVAILABLE = False
    CommunicationProtocol = None


class Orchestrator:
    """
    Multi-agent orchestrator supporting sequential, parallel, and adaptive execution.
    """
    
    def __init__(self, agent_names: List[str], max_agents: int = 19, execution_mode: str = "sequential"):
        """
        Initialize orchestrator.
        
        Args:
            agent_names: List of agent names to load
            max_agents: Maximum number of agents
            execution_mode: Execution mode - "sequential", "parallel", or "adaptive"
        """
        if len(agent_names) > max_agents:
            raise ValueError(f"Too many agents: {len(agent_names)} > {max_agents}")
        self.agent_names = agent_names
        self.agents = [self._load_agent(n) for n in agent_names]
        self.execution_mode = execution_mode
        self.executor = ThreadPoolExecutor(max_workers=min(len(self.agents), 10))

    def _load_agent(self, name: str):
        """Load an agent by name."""
        module = import_module(f"agents.{name}")
        agent_class_name = name.title().replace('_', '') + 'Agent'
        return module.Agent() if hasattr(module, 'Agent') else module.__dict__[agent_class_name]()

    def run(self, task: str, config: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """
        Run agents with the configured execution mode.
        
        Args:
            task: Task description
            config: Optional configuration
            
        Returns:
            Execution results
        """
        config = config or {}
        execution_mode = config.get("execution_mode", self.execution_mode)
        
        if execution_mode == "swarm":
            return self.run_swarm(task, config)
        elif execution_mode == "parallel":
            return self.run_parallel(task, config)
        elif execution_mode == "adaptive":
            return self.run_adaptive(task, config)
        else:
            return self.run_sequential(task, config)

    def run_sequential(self, task: str, config: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """
        Run agents sequentially (original behavior).
        
        Args:
            task: Task description
            config: Optional configuration
            
        Returns:
            Execution results
        """
        context = {"task": task, "outputs": [], "state": {}}
        config = config or {}
        
        # Pre-flight check with Governor
        gov = next((a for a in self.agents if a.__class__.__name__ == "GovernorAgent"), None)
        if gov:
            ok, msg = gov.preflight(task)
            if not ok:
                return {"error": f"Governor blocked task: {msg}"}

        # Load memory if available
        mem = next((a for a in self.agents if a.__class__.__name__ == "AdaptiveMemoryAgent"), None)
        if mem:
            context["state"]["memory"] = mem.load()
        meta_memory = next((a for a in self.agents if a.__class__.__name__ == "MetaMemoryAgent"), None)
        if meta_memory:
            context["state"]["meta_memory"] = meta_memory

        # Execute agents sequentially
        for agent in self.agents:
            if hasattr(agent, "skip_in_main") and getattr(agent, "skip_in_main"):
                continue
            
            try:
                out = agent.run(context)
                context["outputs"].append({
                    "agent": agent.__class__.__name__,
                    "output": out,
                    "status": "success"
                })
                if mem:
                    mem.update(context, out)
                if meta_memory:
                    meta_memory.add_memory(
                        content=str(out),
                        tags=["agent_output"],
                        metadata={"agent_name": agent.__class__.__name__, "task": task}
                    )
                    if hasattr(agent, "reflect"):
                        reflection = agent.reflect({"task": task, "status": "success"})
                        meta_memory.add_memory(
                            content=reflection,
                            tags=["reflection"],
                            metadata={"agent_name": agent.__class__.__name__, "task": task}
                        )
            except Exception as e:
                logger.error(f"Agent {agent.__class__.__name__} failed: {e}", exc_info=True)
                context["outputs"].append({
                    "agent": agent.__class__.__name__,
                    "output": None,
                    "status": "error",
                    "error": str(e)
                })
                # Continue with other agents unless configured to stop on error
                if config.get("stop_on_error", False):
                    break

        # Post-processing
        evalr = next((a for a in self.agents if a.__class__.__name__ == "EvaluatorAgent"), None)
        if evalr:
            context["evaluation"] = evalr.evaluate(context)
            if meta_memory:
                meta_memory.add_memory(
                    content=f"Evaluation summary: {context['evaluation']}",
                    tags=["evaluation"],
                    metadata={"task": task, "agent_name": "EvaluatorAgent"},
                    evaluation=context["evaluation"]
                )

        meta = next((a for a in self.agents if a.__class__.__name__ == "MetaEvolverAgent"), None)
        if meta:
            meta.evolve(self.agents, context)

        return context

    def run_parallel(self, task: str, config: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """
        Run agents in parallel where possible.
        
        Groups agents into execution groups:
        - Sequential: Agents that must run in order (based on dependencies)
        - Parallel: Agents that can run simultaneously
        
        Args:
            task: Task description
            config: Optional configuration
            
        Returns:
            Execution results
        """
        context = {"task": task, "outputs": [], "state": {}}
        config = config or {}
        
        # Pre-flight check
        gov = next((a for a in self.agents if a.__class__.__name__ == "GovernorAgent"), None)
        if gov:
            ok, msg = gov.preflight(task)
            if not ok:
                return {"error": f"Governor blocked task: {msg}"}

        # Load memory
        mem = next((a for a in self.agents if a.__class__.__name__ == "AdaptiveMemoryAgent"), None)
        if mem:
            context["state"]["memory"] = mem.load()
        meta_memory = next((a for a in self.agents if a.__class__.__name__ == "MetaMemoryAgent"), None)
        if meta_memory:
            context["state"]["meta_memory"] = meta_memory

        # Group agents by execution constraints
        sequential_agents = []
        parallel_agents = []
        
        for agent in self.agents:
            if hasattr(agent, "skip_in_main") and getattr(agent, "skip_in_main"):
                continue
            
            # Check if agent has dependencies or must run sequentially
            if hasattr(agent, "requires_sequential") and getattr(agent, "requires_sequential"):
                sequential_agents.append(agent)
            else:
                parallel_agents.append(agent)
        
        # Execute sequential agents first
        for agent in sequential_agents:
            try:
                out = agent.run(context)
                context["outputs"].append({
                    "agent": agent.__class__.__name__,
                    "output": out,
                    "status": "success"
                })
                if mem:
                    mem.update(context, out)
                if meta_memory:
                    meta_memory.add_memory(
                        content=str(out),
                        tags=["agent_output"],
                        metadata={"agent_name": agent.__class__.__name__, "task": task}
                    )
                    if hasattr(agent, "reflect"):
                        reflection = agent.reflect({"task": task, "status": "success"})
                        meta_memory.add_memory(
                            content=reflection,
                            tags=["reflection"],
                            metadata={"agent_name": agent.__class__.__name__, "task": task}
                        )
            except Exception as e:
                logger.error(f"Agent {agent.__class__.__name__} failed: {e}", exc_info=True)
                context["outputs"].append({
                    "agent": agent.__class__.__name__,
                    "output": None,
                    "status": "error",
                    "error": str(e)
                })
        
        # Execute parallel agents concurrently
        if parallel_agents:
            def run_agent(agent):
                """Run a single agent (for thread pool execution)."""
                try:
                    # Create a copy of context for thread safety
                    agent_context = context.copy()
                    out = agent.run(agent_context)
                    return {
                        "agent": agent.__class__.__name__,
                        "output": out,
                        "status": "success"
                    }
                except Exception as e:
                    logger.error(f"Agent {agent.__class__.__name__} failed: {e}", exc_info=True)
                    return {
                        "agent": agent.__class__.__name__,
                        "output": None,
                        "status": "error",
                        "error": str(e)
                    }
            
            # Execute in parallel using thread pool
            futures = [self.executor.submit(run_agent, agent) for agent in parallel_agents]
            results = [future.result() for future in futures]
            
            # Update context with results
            for result in results:
                context["outputs"].append(result)
                if mem and result["status"] == "success":
                    mem.update(context, result["output"])
                if meta_memory and result["status"] == "success":
                    meta_memory.add_memory(
                        content=str(result["output"]),
                        tags=["agent_output"],
                        metadata={"agent_name": result["agent"], "task": task}
                    )

        # Post-processing (sequential)
        evalr = next((a for a in self.agents if a.__class__.__name__ == "EvaluatorAgent"), None)
        if evalr:
            context["evaluation"] = evalr.evaluate(context)
            if meta_memory:
                meta_memory.add_memory(
                    content=f"Evaluation summary: {context['evaluation']}",
                    tags=["evaluation"],
                    metadata={"task": task, "agent_name": "EvaluatorAgent"},
                    evaluation=context["evaluation"]
                )

        meta = next((a for a in self.agents if a.__class__.__name__ == "MetaEvolverAgent"), None)
        if meta:
            meta.evolve(self.agents, context)

        return context

    def run_swarm(self, task: str, config: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """
        Execute task using swarm intelligence.
        
        Uses stigmergic communication and emergent behaviors.
        
        Args:
            task: Task description
            config: Optional configuration
            
        Returns:
            Execution results
        """
        try:
            from core.swarm.swarm_orchestrator import SwarmOrchestrator
            
            swarm_orch = SwarmOrchestrator(base_orchestrator=self)
            
            # Register all agents
            for agent in self.agents:
                agent_id = agent.__class__.__name__
                swarm_orch.register_agent(agent_id, agent)
            
            return swarm_orch.execute_swarm(
                task=task,
                max_iterations=config.get("max_iterations", 10) if config else 10,
                use_stigmergy=config.get("use_stigmergy", True) if config else True
            )
        except ImportError:
            logger.warning("Swarm intelligence not available, falling back to adaptive mode")
            return self.run_adaptive(task, config)
        except Exception as e:
            logger.error(f"Swarm execution failed: {e}")
            return {"error": str(e), "fallback": "adaptive", "result": self.run_adaptive(task, config)}
    
    def run_with_causal_awareness(
        self,
        task: str,
        causal_graph: Any,  # CausalGraph from reasoning module
        config: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        """
        Execute with causal awareness.
        
        Uses causal graph to route tasks intelligently based on cause-effect relationships.
        
        Args:
            task: Task description
            causal_graph: CausalGraph instance
            config: Optional configuration
            
        Returns:
            Execution results
        """
        try:
            from core.reasoning.causal_reasoner import CausalReasoner
            
            reasoner = CausalReasoner(causal_graph)
            
            # Analyze task to identify key variables
            # Simplified: would use NLP to extract variables
            task_variables = self._extract_variables(task)
            
            # Determine best agent based on causal relationships
            selected_agents = []
            for agent in self.agents:
                agent_capabilities = getattr(agent, 'capabilities', [])
                # Check if agent capabilities match causal requirements
                # Simplified heuristic
                if any(cap.lower() in task.lower() for cap in agent_capabilities):
                    selected_agents.append(agent)
            
            if not selected_agents:
                selected_agents = self.agents  # Fallback to all agents
            
            # Execute with selected agents
            context = {"task": task, "outputs": [], "state": {}}
            config = config or {}
            
            for agent in selected_agents:
                try:
                    result = agent.run(context)
                    context["outputs"].append({
                        "agent": agent.__class__.__name__,
                        "result": result
                    })
                except Exception as e:
                    logger.error(f"Agent {agent.__class__.__name__} failed: {e}")
            
            return context
            
        except ImportError:
            logger.warning("Causal reasoning not available, falling back to sequential mode")
            return self.run_sequential(task, config)
        except Exception as e:
            logger.error(f"Causal-aware execution failed: {e}")
            return {"error": str(e), "result": self.run_sequential(task, config)}
    
    def _extract_variables(self, task: str) -> list:
        """Extract variables/concepts from task (simplified)."""
        # Simplified: would use NLP
        words = task.split()
        # Filter for capitalized words or common variable patterns
        variables = [w for w in words if w[0].isupper() and len(w) > 2]
        return variables[:5]  # Return top 5
    
    def run_adaptive(self, task: str, config: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """
        Run agents adaptively based on task requirements and agent capabilities.
        
        This mode:
        1. Analyzes the task to determine required capabilities
        2. Selects relevant agents (skips irrelevant ones)
        3. Determines optimal execution order and parallelism
        4. Executes with dynamic routing
        
        Args:
            task: Task description
            config: Optional configuration
            
        Returns:
            Execution results
        """
        context = {"task": task, "outputs": [], "state": {}}
        config = config or {}
        
        # Pre-flight check
        gov = next((a for a in self.agents if a.__class__.__name__ == "GovernorAgent"), None)
        if gov:
            ok, msg = gov.preflight(task)
            if not ok:
                return {"error": f"Governor blocked task: {msg}"}

        # Simple adaptive logic: select agents based on task keywords
        # In production, this would use ML models for routing
        task_lower = task.lower()
        selected_agents = []
        
        for agent in self.agents:
            if hasattr(agent, "skip_in_main") and getattr(agent, "skip_in_main"):
                continue
            
            # Check if agent is relevant (simple keyword matching)
            # In production, use capability matching or ML-based selection
            agent_name = agent.__class__.__name__.lower()
            
            # Always include certain agents
            if any(keyword in agent_name for keyword in ["governor", "memory", "evaluator"]):
                selected_agents.append(agent)
            # Include reasoning agents for complex tasks
            elif any(keyword in task_lower for keyword in ["reason", "think", "analyze", "solve"]):
                if any(keyword in agent_name for keyword in ["react", "chain", "tree", "planning"]):
                    selected_agents.append(agent)
            # Include specialized agents based on task content
            elif any(keyword in task_lower for keyword in ["search", "lookup", "find"]):
                if "react" in agent_name or "toolformer" in agent_name:
                    selected_agents.append(agent)
            else:
                # Default: include all non-special agents
                if not any(keyword in agent_name for keyword in ["governor", "memory", "evaluator", "meta"]):
                    selected_agents.append(agent)
        
        logger.info(f"Adaptive mode selected {len(selected_agents)} agents for task")
        
        # Execute selected agents (can use parallel execution)
        execution_mode = config.get("adaptive_execution_mode", "parallel")
        if execution_mode == "parallel":
            # Temporarily replace agents list
            original_agents = self.agents
            self.agents = selected_agents
            try:
                result = self.run_parallel(task, config)
            finally:
                self.agents = original_agents
            return result
        else:
            # Sequential execution of selected agents
            original_agents = self.agents
            self.agents = selected_agents
            try:
                result = self.run_sequential(task, config)
            finally:
                self.agents = original_agents
            return result

    def __del__(self):
        """Cleanup thread pool executor."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
