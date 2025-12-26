import random
from typing import Dict, Any, Optional

from utils.logging import get_logger

logger = get_logger(__name__)


class CurriculumAgent:
    """
    Tracks task difficulty and adapts the curriculum using epsilon-greedy promotion/demotion.
    """

    def __init__(self, epsilon: float = 0.1, seed: Optional[int] = None):
        self.epsilon = epsilon
        self.levels = ["easy", "medium", "hard"]
        self.current_level = "medium"
        self.stats = {level: {"success": 0, "total": 0} for level in self.levels}
        self._rng = random.Random(seed)

    def run(self, context: Dict[str, Any]) -> str:
        task = context.get("task", "")
        success = context.get("success")
        meta_memory = context.get("state", {}).get("meta_memory")

        difficulty = self._resolve_difficulty(task, context.get("task_difficulty"))
        if success is not None:
            self._record_performance(difficulty, bool(success))

        previous_level = self.current_level
        next_level = self._adjust_curriculum()

        if next_level != previous_level and meta_memory:
            meta_memory.log_event(
                event_type="curriculum_adjustment",
                payload={
                    "from_level": previous_level,
                    "to_level": next_level,
                    "difficulty": difficulty,
                    "task": task
                },
                tags=["curriculum", "adaptation"]
            )

        logger.info(f"CurriculumAgent processed task at '{difficulty}' -> next '{next_level}'")
        return f"curriculum_agent processed: {task} (next_level={next_level})"

    def reflect(self, context: Dict[str, Any]) -> str:
        lesson = "Adjust difficulty cautiously to avoid oscillation."
        return f"Reflection: curriculum updated to '{self.current_level}'. Lesson learned: {lesson}"

    def _resolve_difficulty(self, task: str, difficulty: Any) -> str:
        if isinstance(difficulty, str) and difficulty in self.levels:
            return difficulty
        if isinstance(difficulty, (int, float)):
            if difficulty < 0.3:
                return "easy"
            if difficulty < 0.7:
                return "medium"
            return "hard"
        # Fallback heuristic based on task length
        token_count = len(task.split())
        if token_count < 8:
            return "easy"
        if token_count < 20:
            return "medium"
        return "hard"

    def _record_performance(self, difficulty: str, success: bool) -> None:
        if difficulty not in self.stats:
            self.stats[difficulty] = {"success": 0, "total": 0}
        self.stats[difficulty]["total"] += 1
        if success:
            self.stats[difficulty]["success"] += 1

    def _adjust_curriculum(self) -> str:
        # Epsilon-greedy selection
        if self._rng.random() < self.epsilon:
            self.current_level = self._rng.choice(self.levels)
            return self.current_level

        stats = self.stats[self.current_level]
        total = stats["total"]
        success_rate = (stats["success"] / total) if total else 0.5

        if success_rate > 0.8 and self.current_level != "hard":
            self.current_level = self.levels[self.levels.index(self.current_level) + 1]
        elif success_rate < 0.3 and self.current_level != "easy":
            self.current_level = self.levels[self.levels.index(self.current_level) - 1]

        return self.current_level


Agent = CurriculumAgent
