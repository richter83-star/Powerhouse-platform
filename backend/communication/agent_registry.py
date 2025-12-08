"""
Agent registry for service discovery and capability tracking.
"""

from typing import Dict, List, Optional, Set, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from threading import Lock

from utils.logging import get_logger
from utils.errors import CommunicationError

logger = get_logger(__name__)


@dataclass
class AgentInfo:
    """
    Information about a registered agent.
    
    Attributes:
        name: Unique agent name/identifier
        agent_type: Type/class of agent (e.g., 'react', 'planning')
        capabilities: List of capabilities this agent provides
        status: Current status ('active', 'idle', 'busy', 'offline')
        metadata: Additional agent-specific metadata
        registered_at: When agent was registered
        last_heartbeat: Last heartbeat timestamp
        message_count: Number of messages processed
    """
    name: str
    agent_type: str
    capabilities: List[str] = field(default_factory=list)
    status: str = "active"
    metadata: Dict[str, Any] = field(default_factory=dict)
    registered_at: datetime = field(default_factory=datetime.now)
    last_heartbeat: datetime = field(default_factory=datetime.now)
    message_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "agent_type": self.agent_type,
            "capabilities": self.capabilities,
            "status": self.status,
            "metadata": self.metadata,
            "registered_at": self.registered_at.isoformat(),
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "message_count": self.message_count
        }


class AgentRegistry:
    """
    Registry for agent discovery and capability tracking.
    
    The registry enables:
    - Agent registration and deregistration
    - Service discovery (find agents by capability)
    - Health monitoring (heartbeats)
    - Load balancing (track agent workload)
    
    This is critical for the modular business model - agents can discover
    what other agents are available in the current deployment.
    """
    
    def __init__(self, heartbeat_timeout_seconds: int = 300):
        """
        Initialize agent registry.
        
        Args:
            heartbeat_timeout_seconds: Time before agent considered offline
        """
        self._agents: Dict[str, AgentInfo] = {}
        self._capabilities_index: Dict[str, Set[str]] = {}
        self._lock = Lock()
        self.heartbeat_timeout_seconds = heartbeat_timeout_seconds
        
        logger.info("AgentRegistry initialized")
    
    def register(
        self,
        name: str,
        agent_type: str,
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentInfo:
        """
        Register an agent with the registry.
        
        Args:
            name: Unique agent name
            agent_type: Type of agent
            capabilities: List of capabilities
            metadata: Additional metadata
            
        Returns:
            AgentInfo: Registered agent information
            
        Raises:
            CommunicationError: If agent name already exists
        """
        with self._lock:
            if name in self._agents:
                raise CommunicationError(f"Agent {name} already registered")
            
            agent_info = AgentInfo(
                name=name,
                agent_type=agent_type,
                capabilities=capabilities or [],
                metadata=metadata or {}
            )
            
            self._agents[name] = agent_info
            
            # Index capabilities
            for capability in agent_info.capabilities:
                if capability not in self._capabilities_index:
                    self._capabilities_index[capability] = set()
                self._capabilities_index[capability].add(name)
            
            logger.info(
                f"Registered agent: {name} (type={agent_type}, "
                f"capabilities={len(agent_info.capabilities)})"
            )
            
            return agent_info
    
    def deregister(self, name: str) -> None:
        """
        Deregister an agent.
        
        Args:
            name: Agent name to deregister
        """
        with self._lock:
            if name not in self._agents:
                logger.warning(f"Attempted to deregister unknown agent: {name}")
                return
            
            agent_info = self._agents[name]
            
            # Remove from capabilities index
            for capability in agent_info.capabilities:
                if capability in self._capabilities_index:
                    self._capabilities_index[capability].discard(name)
                    if not self._capabilities_index[capability]:
                        del self._capabilities_index[capability]
            
            del self._agents[name]
            logger.info(f"Deregistered agent: {name}")
    
    def get_agent(self, name: str) -> Optional[AgentInfo]:
        """
        Get information about a specific agent.
        
        Args:
            name: Agent name
            
        Returns:
            AgentInfo: Agent information or None if not found
        """
        with self._lock:
            return self._agents.get(name)
    
    def list_agents(
        self,
        agent_type: Optional[str] = None,
        status: Optional[str] = None,
        capability: Optional[str] = None
    ) -> List[AgentInfo]:
        """
        List agents with optional filtering.
        
        Args:
            agent_type: Filter by agent type
            status: Filter by status
            capability: Filter by capability
            
        Returns:
            List[AgentInfo]: List of matching agents
        """
        with self._lock:
            agents = list(self._agents.values())
        
        if agent_type:
            agents = [a for a in agents if a.agent_type == agent_type]
        
        if status:
            agents = [a for a in agents if a.status == status]
        
        if capability:
            agents = [a for a in agents if capability in a.capabilities]
        
        return agents
    
    def find_by_capability(self, capability: str) -> List[str]:
        """
        Find all agents with a specific capability.
        
        Args:
            capability: Capability to search for
            
        Returns:
            List[str]: List of agent names
        """
        with self._lock:
            return list(self._capabilities_index.get(capability, set()))
    
    def update_status(self, name: str, status: str) -> None:
        """
        Update agent status.
        
        Args:
            name: Agent name
            status: New status ('active', 'idle', 'busy', 'offline')
        """
        with self._lock:
            if name in self._agents:
                self._agents[name].status = status
                logger.debug(f"Updated status for {name}: {status}")
    
    def heartbeat(self, name: str) -> None:
        """
        Record a heartbeat from an agent.
        
        Args:
            name: Agent name
        """
        with self._lock:
            if name in self._agents:
                self._agents[name].last_heartbeat = datetime.now()
                if self._agents[name].status == "offline":
                    self._agents[name].status = "active"
    
    def increment_message_count(self, name: str) -> None:
        """
        Increment message count for an agent.
        
        Args:
            name: Agent name
        """
        with self._lock:
            if name in self._agents:
                self._agents[name].message_count += 1
    
    def check_health(self) -> Dict[str, str]:
        """
        Check health of all agents based on heartbeats.
        
        Returns:
            dict: Map of agent names to health status
        """
        cutoff = datetime.now() - timedelta(seconds=self.heartbeat_timeout_seconds)
        health_status = {}
        
        with self._lock:
            for name, agent_info in self._agents.items():
                if agent_info.last_heartbeat < cutoff:
                    agent_info.status = "offline"
                    health_status[name] = "offline"
                else:
                    health_status[name] = agent_info.status
        
        return health_status
    
    def get_least_busy_agent(
        self,
        agent_type: Optional[str] = None,
        capability: Optional[str] = None
    ) -> Optional[str]:
        """
        Get the least busy agent matching criteria.
        
        Useful for load balancing.
        
        Args:
            agent_type: Filter by agent type
            capability: Filter by capability
            
        Returns:
            str: Name of least busy agent or None
        """
        agents = self.list_agents(agent_type=agent_type, capability=capability)
        
        # Filter to only active/idle agents
        agents = [a for a in agents if a.status in ("active", "idle")]
        
        if not agents:
            return None
        
        # Sort by message count (ascending)
        agents.sort(key=lambda a: a.message_count)
        return agents[0].name
    
    def get_capabilities(self) -> Dict[str, List[str]]:
        """
        Get all capabilities and the agents that provide them.
        
        Returns:
            dict: Map of capability to list of agent names
        """
        with self._lock:
            return {
                capability: list(agents)
                for capability, agents in self._capabilities_index.items()
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get registry statistics.
        
        Returns:
            dict: Statistics about registered agents
        """
        with self._lock:
            return {
                "total_agents": len(self._agents),
                "agents_by_type": self._count_by_type(),
                "agents_by_status": self._count_by_status(),
                "total_capabilities": len(self._capabilities_index),
                "total_messages_processed": sum(a.message_count for a in self._agents.values())
            }
    
    def _count_by_type(self) -> Dict[str, int]:
        """Count agents by type."""
        counts = {}
        for agent in self._agents.values():
            counts[agent.agent_type] = counts.get(agent.agent_type, 0) + 1
        return counts
    
    def _count_by_status(self) -> Dict[str, int]:
        """Count agents by status."""
        counts = {}
        for agent in self._agents.values():
            counts[agent.status] = counts.get(agent.status, 0) + 1
        return counts
    
    def reset(self) -> None:
        """Reset the registry (useful for testing)."""
        with self._lock:
            self._agents.clear()
            self._capabilities_index.clear()
            logger.info("AgentRegistry reset")
