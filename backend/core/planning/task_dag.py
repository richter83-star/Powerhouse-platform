"""
Task DAG: Represents hierarchical task structure with dependencies.
"""

from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False

from utils.logging import get_logger

logger = get_logger(__name__)


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TaskNode:
    """Represents a task node in the DAG."""
    id: str
    description: str
    task_type: str = "general"
    status: TaskStatus = TaskStatus.PENDING
    dependencies: Set[str] = field(default_factory=set)
    subtasks: List[str] = field(default_factory=list)  # IDs of child tasks
    parent_id: Optional[str] = None
    depth: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Any] = None
    error: Optional[str] = None


class TaskDAG:
    """
    Directed Acyclic Graph representing hierarchical task structure.
    
    Tasks can have dependencies (must complete before) and subtasks (children).
    """
    
    def __init__(self, root_task: TaskNode):
        """
        Initialize task DAG with root task.
        
        Args:
            root_task: Root task node
        """
        self.tasks: Dict[str, TaskNode] = {root_task.id: root_task}
        self.root_id = root_task.id
        
        if NETWORKX_AVAILABLE:
            self.graph = nx.DiGraph()
            self.graph.add_node(root_task.id)
        else:
            self.graph = None
        
        self.logger = get_logger(__name__)
    
    def add_task(self, task: TaskNode) -> None:
        """Add a task to the DAG."""
        self.tasks[task.id] = task
        
        if self.graph is not None:
            self.graph.add_node(task.id)
        
        # Add dependency edges
        for dep_id in task.dependencies:
            if dep_id in self.tasks:
                self.tasks[dep_id].subtasks.append(task.id)
                if self.graph is not None:
                    self.graph.add_edge(dep_id, task.id)
        
        # Add parent relationship
        if task.parent_id:
            parent = self.tasks.get(task.parent_id)
            if parent:
                parent.subtasks.append(task.id)
    
    def get_ready_tasks(self) -> List[TaskNode]:
        """
        Get tasks that are ready to execute (dependencies satisfied).
        
        Returns:
            List of tasks ready to run
        """
        ready = []
        
        for task in self.tasks.values():
            if task.status != TaskStatus.PENDING:
                continue
            
            # Check if all dependencies are completed
            all_deps_complete = all(
                self.tasks[dep_id].status == TaskStatus.COMPLETED
                for dep_id in task.dependencies
                if dep_id in self.tasks
            )
            
            if all_deps_complete:
                task.status = TaskStatus.READY
                ready.append(task)
        
        return ready
    
    def update_task_status(self, task_id: str, status: TaskStatus, result: Any = None, error: Optional[str] = None) -> None:
        """Update task status."""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = status
            task.result = result
            task.error = error
    
    def get_tasks_by_depth(self, depth: int) -> List[TaskNode]:
        """Get all tasks at a specific depth level."""
        return [task for task in self.tasks.values() if task.depth == depth]
    
    def get_topological_order(self) -> List[TaskNode]:
        """
        Get tasks in topological order (dependencies before dependents).
        
        Returns:
            List of tasks in execution order
        """
        if self.graph is not None:
            try:
                order = list(nx.topological_sort(self.graph))
                return [self.tasks[task_id] for task_id in order if task_id in self.tasks]
            except nx.NetworkXError:
                # Cycle detected
                self.logger.warning("Cycle detected in task DAG")
                return list(self.tasks.values())
        
        # Fallback: simple ordering by dependencies
        ordered = []
        remaining = set(self.tasks.keys())
        
        while remaining:
            # Find tasks with no remaining dependencies
            ready = [
                task_id for task_id in remaining
                if all(dep not in remaining for dep in self.tasks[task_id].dependencies)
            ]
            
            if not ready:
                # Cycle or error
                ordered.extend([self.tasks[task_id] for task_id in remaining])
                break
            
            ordered.extend([self.tasks[task_id] for task_id in ready])
            remaining -= set(ready)
        
        return ordered
    
    def get_subtree(self, task_id: str) -> 'TaskDAG':
        """
        Get subtree rooted at a specific task.
        
        Args:
            task_id: Root task ID for subtree
            
        Returns:
            New TaskDAG containing subtree
        """
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        root = self.tasks[task_id]
        subtree = TaskDAG(root)
        
        # Collect all descendant tasks
        def collect_descendants(task_id: str, visited: Set[str]):
            if task_id in visited:
                return
            visited.add(task_id)
            
            task = self.tasks[task_id]
            for child_id in task.subtasks:
                if child_id in self.tasks:
                    subtree.add_task(self.tasks[child_id])
                    collect_descendants(child_id, visited)
        
        collect_descendants(task_id, set())
        return subtree
    
    def is_complete(self) -> bool:
        """Check if all tasks are completed."""
        return all(
            task.status in (TaskStatus.COMPLETED, TaskStatus.SKIPPED)
            for task in self.tasks.values()
        )
    
    def to_dict(self) -> Dict:
        """Export DAG to dictionary."""
        return {
            "root_id": self.root_id,
            "tasks": {
                task_id: {
                    "id": task.id,
                    "description": task.description,
                    "task_type": task.task_type,
                    "status": task.status.value,
                    "dependencies": list(task.dependencies),
                    "subtasks": task.subtasks,
                    "parent_id": task.parent_id,
                    "depth": task.depth,
                    "metadata": task.metadata
                }
                for task_id, task in self.tasks.items()
            }
        }

