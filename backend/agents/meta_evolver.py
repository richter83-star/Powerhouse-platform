import copy
import random
import time
from typing import Dict, Any, Optional, List

from utils.logging import get_logger

logger = get_logger(__name__)


class MetaEvolverAgent:
    """
    Mutates agent configs based on evaluation feedback.
    """

    skip_in_main = True

    def __init__(
        self,
        memory_agent: Optional[Any] = None,
        evolve_every_n: int = 5,
        min_score: float = 0.5,
        seed: Optional[int] = None
    ):
        self.memory_agent = memory_agent
        self.evolve_every_n = evolve_every_n
        self.min_score = min_score
        self._evolution_counter = 0
        self.mutation_log: List[Dict[str, Any]] = []
        self._rng = random.Random(seed)

    def mutate(self, agent_config: Dict[str, Any]) -> Dict[str, Any]:
        mutated = copy.deepcopy(agent_config) if agent_config else {}
        mutated.setdefault("learning_rate", 0.001)
        mutated.setdefault("memory_size", 256)
        mutated.setdefault("max_retries", 3)

        # Randomly tweak within safe bounds
        mutated["learning_rate"] = max(1e-5, min(mutated["learning_rate"] * self._rng.uniform(0.8, 1.2), 0.1))
        mutated["memory_size"] = int(max(32, min(mutated["memory_size"] + self._rng.randint(-32, 64), 2048)))
        mutated["max_retries"] = int(max(0, min(mutated["max_retries"] + self._rng.choice([-1, 0, 1]), 10)))

        return mutated

    def evolve(self, agents, context):
        self._evolution_counter += 1
        if self._evolution_counter % max(self.evolve_every_n, 1) != 0:
            return False

        memory_agent = self.memory_agent or context.get("state", {}).get("meta_memory")
        scores = memory_agent.get_agent_performance() if memory_agent else {}
        mutated_any = False

        for agent in agents:
            agent_name = agent.__class__.__name__
            score = scores.get(agent_name)
            if score is None or score >= self.min_score:
                continue

            config = getattr(agent, "config", None) or getattr(agent, "metadata", {}) or {}
            mutated = self.mutate(config)

            if hasattr(agent, "config"):
                agent.config = mutated
            elif hasattr(agent, "metadata"):
                agent.metadata = mutated

            mutation_record = {
                "agent_name": agent_name,
                "previous_score": score,
                "new_config": mutated,
                "timestamp": time.time()
            }
            self.mutation_log.append(mutation_record)
            mutated_any = True

            if memory_agent:
                memory_agent.log_event(
                    event_type="agent_mutation",
                    payload=mutation_record,
                    tags=["mutation", "meta_evolution"]
                )

            logger.info(f"Mutated agent config for {agent_name} (score={score:.2f})")

        return mutated_any
