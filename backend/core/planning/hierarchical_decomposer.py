"""
Hierarchical Task Decomposition: Recursively breaks down tasks into subtasks.

Uses LLM to intelligently decompose complex tasks into manageable subtasks.
"""

from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from datetime import datetime
import uuid

from core.planning.task_dag import TaskDAG, TaskNode, TaskStatus
from llm.base import BaseLLMProvider
from config.llm_config import LLMConfig
from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Subtask:
    """Represents a decomposed subtask."""
    description: str
    task_type: str
    dependencies: List[str] = None  # Descriptions of dependent subtasks
    estimated_complexity: float = 0.5  # 0.0-1.0
    estimated_duration: Optional[float] = None  # Estimated seconds


class TaskDecomposer:
    """
    Hierarchically decomposes complex tasks into subtasks.
    
    Features:
    - Recursive decomposition
    - Dependency detection
    - Complexity estimation
    - LLM-powered intelligent breakdown
    """
    
    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None, max_depth: int = 5):
        """
        Initialize task decomposer.
        
        Args:
            llm_provider: LLM provider for decomposition (uses default if None)
            max_depth: Maximum recursion depth
        """
        self.llm = llm_provider or LLMConfig.get_llm_provider("task_decomposition")
        self.max_depth = max_depth
        self.logger = get_logger(__name__)
    
    def decompose(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None,
        max_subtasks: int = 10
    ) -> TaskDAG:
        """
        Decompose a task into hierarchical subtasks.
        
        Args:
            task_description: Task to decompose
            context: Optional context information
            max_subtasks: Maximum subtasks per level
            
        Returns:
            TaskDAG representing decomposed task structure
        """
        # Create root task
        root_task = TaskNode(
            id=str(uuid.uuid4()),
            description=task_description,
            task_type="root",
            depth=0
        )
        
        dag = TaskDAG(root_task)
        
        # Recursively decompose
        self._decompose_recursive(
            root_task.id,
            task_description,
            dag,
            depth=0,
            context=context,
            max_subtasks=max_subtasks
        )
        
        return dag
    
    def _decompose_recursive(
        self,
        parent_id: str,
        task_description: str,
        dag: TaskDAG,
        depth: int,
        context: Optional[Dict[str, Any]] = None,
        max_subtasks: int = 10
    ) -> None:
        """
        Recursively decompose a task.
        
        Args:
            parent_id: Parent task ID
            task_description: Task to decompose
            dag: Task DAG to add to
            depth: Current depth
            context: Context information
            max_subtasks: Maximum subtasks
        """
        if depth >= self.max_depth:
            return  # Stop recursion
        
        # Check if task is simple enough (heuristic)
        if self._is_simple_task(task_description):
            return  # Don't decompose further
        
        # Use LLM to decompose task
        subtasks = self._llm_decompose(task_description, context, max_subtasks)
        
        if not subtasks:
            return
        
        # Create task nodes
        task_descriptions = {st.description for st in subtasks}
        task_map = {}  # description -> task_id
        
        for subtask in subtasks:
            task_id = str(uuid.uuid4())
            task_map[subtask.description] = task_id
            
            # Resolve dependencies (convert descriptions to IDs)
            dependency_ids = set()
            if subtask.dependencies:
                for dep_desc in subtask.dependencies:
                    # Find matching task in current level or parent levels
                    dep_id = self._find_task_by_description(dag, dep_desc)
                    if dep_id:
                        dependency_ids.add(dep_id)
            
            task_node = TaskNode(
                id=task_id,
                description=subtask.description,
                task_type=subtask.task_type,
                parent_id=parent_id,
                depth=depth + 1,
                dependencies=dependency_ids,
                metadata={
                    "complexity": subtask.estimated_complexity,
                    "estimated_duration": subtask.estimated_duration
                }
            )
            
            dag.add_task(task_node)
        
        # Recursively decompose each subtask if complex enough
        for subtask in subtasks:
            task_id = task_map[subtask.description]
            if subtask.estimated_complexity > 0.3:  # Threshold for further decomposition
                self._decompose_recursive(
                    task_id,
                    subtask.description,
                    dag,
                    depth + 1,
                    context,
                    max_subtasks
                )
    
    def _llm_decompose(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]],
        max_subtasks: int
    ) -> List[Subtask]:
        """
        Use LLM to decompose task into subtasks.
        
        Args:
            task_description: Task to decompose
            context: Context information
            max_subtasks: Maximum subtasks
            
        Returns:
            List of Subtask objects
        """
        prompt = f"""Break down the following task into {max_subtasks} or fewer subtasks.

Task: {task_description}

{f"Context: {context}" if context else ""}

For each subtask, provide:
1. A clear description
2. Task type (e.g., "research", "analysis", "implementation", "validation")
3. Dependencies (which subtasks must complete first)
4. Estimated complexity (0.0-1.0)
5. Estimated duration in seconds (optional)

Format as JSON array:
[
  {{
    "description": "Subtask description",
    "task_type": "type",
    "dependencies": ["dependency description 1", ...],
    "estimated_complexity": 0.5,
    "estimated_duration": 60
  }},
  ...
]

Return only valid JSON, no markdown formatting.
"""
        
        try:
            response = self.llm.invoke(
                prompt=prompt,
                temperature=0.7,
                max_tokens=2000,
                json_mode=True
            )
            
            import json
            subtasks_data = json.loads(response.content)
            
            subtasks = []
            for st_data in subtasks_data:
                subtask = Subtask(
                    description=st_data.get("description", ""),
                    task_type=st_data.get("task_type", "general"),
                    dependencies=st_data.get("dependencies", []),
                    estimated_complexity=st_data.get("estimated_complexity", 0.5),
                    estimated_duration=st_data.get("estimated_duration")
                )
                subtasks.append(subtask)
            
            self.logger.info(f"Decomposed task into {len(subtasks)} subtasks")
            return subtasks
            
        except Exception as e:
            self.logger.error(f"LLM decomposition failed: {e}")
            # Fallback: simple heuristic decomposition
            return self._heuristic_decompose(task_description, max_subtasks)
    
    def _heuristic_decompose(self, task_description: str, max_subtasks: int) -> List[Subtask]:
        """Heuristic fallback decomposition."""
        # Simple keyword-based decomposition
        subtasks = []
        
        keywords = {
            "research": ["research", "investigate", "study", "analyze"],
            "implementation": ["implement", "build", "create", "develop"],
            "testing": ["test", "validate", "verify", "check"],
            "documentation": ["document", "write", "describe"]
        }
        
        task_lower = task_description.lower()
        for task_type, keywords_list in keywords.items():
            if any(kw in task_lower for kw in keywords_list):
                subtasks.append(Subtask(
                    description=f"{task_type.capitalize()}: {task_description}",
                    task_type=task_type,
                    estimated_complexity=0.5
                ))
        
        if not subtasks:
            # Default: single subtask
            subtasks.append(Subtask(
                description=task_description,
                task_type="general",
                estimated_complexity=0.5
            ))
        
        return subtasks[:max_subtasks]
    
    def _is_simple_task(self, task_description: str) -> bool:
        """Check if task is simple enough to not decompose further."""
        # Heuristic: short tasks with simple verbs are likely atomic
        simple_keywords = ["fetch", "get", "read", "write", "save", "delete", "update"]
        task_lower = task_description.lower()
        
        # If task is short and uses simple verb, consider it atomic
        words = task_description.split()
        if len(words) < 5 and any(kw in task_lower for kw in simple_keywords):
            return True
        
        return False
    
    def _find_task_by_description(self, dag: TaskDAG, description: str) -> Optional[str]:
        """Find task ID by description (fuzzy matching)."""
        description_lower = description.lower()
        
        for task_id, task in dag.tasks.items():
            if description_lower in task.description.lower() or task.description.lower() in description_lower:
                return task_id
        
        return None

