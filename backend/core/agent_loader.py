"""
Dynamic agent loading system.
"""

import importlib
import inspect
from typing import Dict, List, Optional, Type, Any
from pathlib import Path

from .base_agent import BaseAgent
from communication import CommunicationProtocol
from llm import BaseLLMProvider
from utils.logging import get_logger
from utils.errors import ConfigurationError

logger = get_logger(__name__)


class AgentLoader:
    """
    Dynamic agent loader.
    
    Loads agent classes from the agents directory and instantiates them
    based on configuration. This enables the modular business model where
    clients can select which agents they want.
    """
    
    def __init__(self, agents_package: str = "agents"):
        """
        Initialize agent loader.
        
        Args:
            agents_package: Python package containing agent modules
        """
        self.agents_package = agents_package
        self._agent_classes: Dict[str, Type[BaseAgent]] = {}
        self._discover_agents()
    
    def _discover_agents(self) -> None:
        """
        Discover all agent classes in the agents package.
        
        Scans the agents directory and finds all classes that inherit
        from BaseAgent.
        """
        try:
            # Import the agents package
            package = importlib.import_module(self.agents_package)
            package_path = Path(package.__file__).parent
            
            # Find all Python files in the package
            for module_file in package_path.glob("*.py"):
                if module_file.name.startswith("_"):
                    continue
                
                module_name = module_file.stem
                full_module_name = f"{self.agents_package}.{module_name}"
                
                try:
                    # Import the module
                    module = importlib.import_module(full_module_name)
                    
                    # Find all classes that inherit from BaseAgent
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (issubclass(obj, BaseAgent) and 
                            obj is not BaseAgent and
                            obj.__module__ == full_module_name):
                            
                            # Use module name as agent type
                            agent_type = module_name
                            self._agent_classes[agent_type] = obj
                            logger.debug(f"Discovered agent: {agent_type} -> {obj.__name__}")
                
                except Exception as e:
                    logger.warning(f"Failed to load module {full_module_name}: {e}")
            
            logger.info(f"Discovered {len(self._agent_classes)} agent types")
            
        except Exception as e:
            logger.error(f"Failed to discover agents: {e}")
            raise ConfigurationError(f"Agent discovery failed: {str(e)}")
    
    def get_available_agents(self) -> List[str]:
        """
        Get list of available agent types.
        
        Returns:
            List[str]: List of agent type names
        """
        return list(self._agent_classes.keys())
    
    def load_agent(
        self,
        agent_type: str,
        name: Optional[str] = None,
        protocol: Optional[CommunicationProtocol] = None,
        llm_provider: Optional[BaseLLMProvider] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> BaseAgent:
        """
        Load and instantiate an agent.
        
        Args:
            agent_type: Type of agent to load
            name: Unique name for this agent instance
            protocol: Communication protocol
            llm_provider: LLM provider
            config: Additional configuration
            
        Returns:
            BaseAgent: Instantiated agent
            
        Raises:
            ConfigurationError: If agent type not found
        """
        if agent_type not in self._agent_classes:
            available = ", ".join(self.get_available_agents())
            raise ConfigurationError(
                f"Unknown agent type: {agent_type}. Available: {available}"
            )
        
        agent_class = self._agent_classes[agent_type]
        
        # Generate name if not provided
        if not name:
            name = f"{agent_type}_agent"
        
        # Get capabilities from agent class if available
        capabilities = getattr(agent_class, "CAPABILITIES", [])
        
        try:
            # Instantiate the agent
            agent = agent_class(
                name=name,
                agent_type=agent_type,
                capabilities=capabilities,
                protocol=protocol,
                llm_provider=llm_provider,
                metadata=config or {}
            )
            
            logger.info(f"Loaded agent: {name} (type={agent_type})")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to instantiate agent {agent_type}: {e}")
            raise ConfigurationError(f"Agent instantiation failed: {str(e)}")
    
    def load_agents(
        self,
        agent_types: List[str],
        protocol: Optional[CommunicationProtocol] = None,
        llm_provider: Optional[BaseLLMProvider] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> List[BaseAgent]:
        """
        Load multiple agents.
        
        Args:
            agent_types: List of agent types to load
            protocol: Communication protocol
            llm_provider: LLM provider
            config: Configuration dict (can have per-agent config)
            
        Returns:
            List[BaseAgent]: List of instantiated agents
        """
        agents = []
        config = config or {}
        
        for agent_type in agent_types:
            # Get agent-specific config if available
            agent_config = config.get(agent_type, {})
            
            # Generate unique name
            name = f"{agent_type}_agent"
            
            try:
                agent = self.load_agent(
                    agent_type=agent_type,
                    name=name,
                    protocol=protocol,
                    llm_provider=llm_provider,
                    config=agent_config
                )
                agents.append(agent)
            except Exception as e:
                logger.error(f"Failed to load agent {agent_type}: {e}")
                # Continue loading other agents
        
        logger.info(f"Loaded {len(agents)}/{len(agent_types)} agents")
        return agents
    
    def validate_agent_types(self, agent_types: List[str]) -> tuple[List[str], List[str]]:
        """
        Validate a list of agent types.
        
        Args:
            agent_types: List of agent types to validate
            
        Returns:
            tuple: (valid_types, invalid_types)
        """
        valid = []
        invalid = []
        
        for agent_type in agent_types:
            if agent_type in self._agent_classes:
                valid.append(agent_type)
            else:
                invalid.append(agent_type)
        
        return valid, invalid
    
    def get_agent_info(self, agent_type: str) -> Optional[Dict[str, Any]]:
        """
        Get information about an agent type.
        
        Args:
            agent_type: Agent type
            
        Returns:
            dict: Agent information or None
        """
        if agent_type not in self._agent_classes:
            return None
        
        agent_class = self._agent_classes[agent_type]
        
        return {
            "type": agent_type,
            "class_name": agent_class.__name__,
            "module": agent_class.__module__,
            "capabilities": getattr(agent_class, "CAPABILITIES", []),
            "description": agent_class.__doc__ or "No description available"
        }
    
    def reload_agents(self) -> None:
        """
        Reload agent discovery.
        
        Useful for development when agents are modified.
        """
        self._agent_classes.clear()
        self._discover_agents()
        logger.info("Agents reloaded")
