"""
Shared context manager for inter-agent state sharing.
"""

from typing import Any, Dict, Optional, List, Set
from datetime import datetime
from threading import Lock
from copy import deepcopy

from utils.logging import get_logger

logger = get_logger(__name__)


class SharedContext:
    """
    Shared context manager for agent coordination.
    
    The shared context provides:
    - Global state accessible to all agents
    - Namespaced state (per-agent private state)
    - State history and versioning
    - Thread-safe read/write operations
    - State change notifications
    
    This enables agents to coordinate by sharing information without
    direct message passing.
    """
    
    def __init__(self, enable_history: bool = True, max_history_size: int = 1000):
        """
        Initialize shared context.
        
        Args:
            enable_history: Whether to track state changes
            max_history_size: Maximum history entries to keep
        """
        self._global_state: Dict[str, Any] = {}
        self._agent_states: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
        self._history: List[Dict[str, Any]] = []
        self._watchers: Dict[str, Set[str]] = {}  # key -> set of agent names
        
        self.enable_history = enable_history
        self.max_history_size = max_history_size
        
        logger.info("SharedContext initialized")
    
    def set(
        self,
        key: str,
        value: Any,
        agent_name: Optional[str] = None,
        namespace: str = "global"
    ) -> None:
        """
        Set a value in the shared context.
        
        Args:
            key: Key to set
            value: Value to store
            agent_name: Agent making the change (for history)
            namespace: Namespace ('global' or agent-specific)
        """
        with self._lock:
            old_value = None
            
            if namespace == "global":
                old_value = self._global_state.get(key)
                self._global_state[key] = value
                full_key = key
            else:
                if namespace not in self._agent_states:
                    self._agent_states[namespace] = {}
                old_value = self._agent_states[namespace].get(key)
                self._agent_states[namespace][key] = value
                full_key = f"{namespace}.{key}"
            
            # Record history
            if self.enable_history:
                self._add_history_entry(
                    action="set",
                    key=full_key,
                    old_value=old_value,
                    new_value=value,
                    agent_name=agent_name
                )
            
            # Notify watchers
            self._notify_watchers(full_key, value, agent_name)
            
            logger.debug(f"Set {full_key} = {value} (by {agent_name or 'system'})")
    
    def get(
        self,
        key: str,
        default: Any = None,
        namespace: str = "global"
    ) -> Any:
        """
        Get a value from the shared context.
        
        Args:
            key: Key to retrieve
            default: Default value if key not found
            namespace: Namespace to search
            
        Returns:
            Any: Value or default
        """
        with self._lock:
            if namespace == "global":
                return self._global_state.get(key, default)
            else:
                return self._agent_states.get(namespace, {}).get(key, default)
    
    def get_all(self, namespace: str = "global") -> Dict[str, Any]:
        """
        Get all values in a namespace.
        
        Args:
            namespace: Namespace to retrieve
            
        Returns:
            dict: Copy of all values in namespace
        """
        with self._lock:
            if namespace == "global":
                return deepcopy(self._global_state)
            else:
                return deepcopy(self._agent_states.get(namespace, {}))
    
    def delete(
        self,
        key: str,
        agent_name: Optional[str] = None,
        namespace: str = "global"
    ) -> bool:
        """
        Delete a key from the context.
        
        Args:
            key: Key to delete
            agent_name: Agent making the change
            namespace: Namespace
            
        Returns:
            bool: True if key existed and was deleted
        """
        with self._lock:
            existed = False
            old_value = None
            
            if namespace == "global":
                if key in self._global_state:
                    old_value = self._global_state.pop(key)
                    existed = True
                    full_key = key
            else:
                if namespace in self._agent_states and key in self._agent_states[namespace]:
                    old_value = self._agent_states[namespace].pop(key)
                    existed = True
                    full_key = f"{namespace}.{key}"
            
            if existed and self.enable_history:
                self._add_history_entry(
                    action="delete",
                    key=full_key,
                    old_value=old_value,
                    new_value=None,
                    agent_name=agent_name
                )
            
            if existed:
                logger.debug(f"Deleted {full_key} (by {agent_name or 'system'})")
            
            return existed
    
    def update(
        self,
        updates: Dict[str, Any],
        agent_name: Optional[str] = None,
        namespace: str = "global"
    ) -> None:
        """
        Update multiple values at once.
        
        Args:
            updates: Dictionary of key-value pairs to update
            agent_name: Agent making the changes
            namespace: Namespace
        """
        for key, value in updates.items():
            self.set(key, value, agent_name=agent_name, namespace=namespace)
    
    def has(self, key: str, namespace: str = "global") -> bool:
        """
        Check if a key exists.
        
        Args:
            key: Key to check
            namespace: Namespace
            
        Returns:
            bool: True if key exists
        """
        with self._lock:
            if namespace == "global":
                return key in self._global_state
            else:
                return namespace in self._agent_states and key in self._agent_states[namespace]
    
    def keys(self, namespace: str = "global") -> List[str]:
        """
        Get all keys in a namespace.
        
        Args:
            namespace: Namespace
            
        Returns:
            List[str]: List of keys
        """
        with self._lock:
            if namespace == "global":
                return list(self._global_state.keys())
            else:
                return list(self._agent_states.get(namespace, {}).keys())
    
    def watch(self, key: str, agent_name: str) -> None:
        """
        Watch a key for changes.
        
        The agent will be notified when this key changes.
        
        Args:
            key: Key to watch
            agent_name: Agent to notify
        """
        with self._lock:
            if key not in self._watchers:
                self._watchers[key] = set()
            self._watchers[key].add(agent_name)
            logger.debug(f"Agent {agent_name} watching key: {key}")
    
    def unwatch(self, key: str, agent_name: str) -> None:
        """
        Stop watching a key.
        
        Args:
            key: Key to stop watching
            agent_name: Agent name
        """
        with self._lock:
            if key in self._watchers:
                self._watchers[key].discard(agent_name)
                if not self._watchers[key]:
                    del self._watchers[key]
    
    def get_history(
        self,
        key: Optional[str] = None,
        agent_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get state change history.
        
        Args:
            key: Filter by key
            agent_name: Filter by agent
            limit: Maximum entries to return
            
        Returns:
            List[dict]: History entries
        """
        with self._lock:
            history = self._history.copy()
        
        if key:
            history = [h for h in history if h["key"] == key]
        
        if agent_name:
            history = [h for h in history if h["agent_name"] == agent_name]
        
        return history[-limit:]
    
    def clear(self, namespace: Optional[str] = None) -> None:
        """
        Clear context.
        
        Args:
            namespace: Specific namespace to clear, or None for all
        """
        with self._lock:
            if namespace is None:
                self._global_state.clear()
                self._agent_states.clear()
                logger.info("Cleared all context")
            elif namespace == "global":
                self._global_state.clear()
                logger.info("Cleared global context")
            elif namespace in self._agent_states:
                self._agent_states[namespace].clear()
                logger.info(f"Cleared context for namespace: {namespace}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get context statistics.
        
        Returns:
            dict: Statistics
        """
        with self._lock:
            return {
                "global_keys": len(self._global_state),
                "agent_namespaces": len(self._agent_states),
                "total_agent_keys": sum(len(state) for state in self._agent_states.values()),
                "history_size": len(self._history),
                "watched_keys": len(self._watchers),
                "total_watchers": sum(len(watchers) for watchers in self._watchers.values())
            }
    
    def _add_history_entry(
        self,
        action: str,
        key: str,
        old_value: Any,
        new_value: Any,
        agent_name: Optional[str]
    ) -> None:
        """Add an entry to the history."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "key": key,
            "old_value": old_value,
            "new_value": new_value,
            "agent_name": agent_name
        }
        
        self._history.append(entry)
        
        # Trim history if needed
        if len(self._history) > self.max_history_size:
            self._history = self._history[-self.max_history_size:]
    
    def _notify_watchers(self, key: str, value: Any, agent_name: Optional[str]) -> None:
        """Notify agents watching this key."""
        if key in self._watchers:
            watchers = self._watchers[key].copy()
            for watcher in watchers:
                if watcher != agent_name:  # Don't notify the agent that made the change
                    logger.debug(f"Notifying {watcher} of change to {key}")
    
    def reset(self) -> None:
        """Reset the context (useful for testing)."""
        with self._lock:
            self._global_state.clear()
            self._agent_states.clear()
            self._history.clear()
            self._watchers.clear()
            logger.info("SharedContext reset")
