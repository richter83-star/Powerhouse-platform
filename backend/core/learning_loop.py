"""
LearningLoop — closes the agent feedback cycle.

After every orchestrator run this background thread:
  1. Pulls the evaluation score and per-agent outputs from context
  2. Tracks a rolling average and computes a compounding multiplier vs baseline
  3. Nudges DynamicConfigManager when the system over/under-performs
  4. Triggers MetaEvolverAgent every N runs to mutate stale agent configs
  5. Pushes agent-outcome events into MetaMemoryAgent for future retrieval

Result: every orchestrator run is informed by every prior run, creating
genuine compounding improvement rather than stateless one-shot execution.
"""

import threading
import time
from collections import deque
from typing import Any, Dict, Optional

from utils.logging import get_logger

logger = get_logger(__name__)


class LearningLoop:
    """
    Lightweight always-on background loop that closes the agent feedback cycle.

    Usage::

        loop = LearningLoop(meta_memory=..., config_manager=..., meta_evolver=...)
        loop.start()

        # After every orchestrator run:
        loop.record(context)

        # Inspect compounding gain at any time:
        print(loop.multiplier)   # 1.0 at baseline, >1.0 as system improves
    """

    _WINDOW = 20  # rolling window for score averaging

    def __init__(
        self,
        meta_memory=None,
        config_manager=None,
        meta_evolver=None,
        evolve_every: int = 5,
    ):
        self.meta_memory = meta_memory
        self.config_manager = config_manager
        self.meta_evolver = meta_evolver
        self.evolve_every = evolve_every

        self._lock = threading.Lock()
        self._run_count: int = 0
        self._scores: deque = deque(maxlen=self._WINDOW)
        self._baseline: Optional[float] = None
        self.multiplier: float = 1.0

        self._queue: deque = deque()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the background processing thread."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._loop, daemon=True, name="LearningLoop"
        )
        self._thread.start()
        logger.info("LearningLoop started")

    def stop(self) -> None:
        """Signal the background thread to exit."""
        self._stop_event.set()

    def record(self, context: Dict[str, Any]) -> None:
        """
        Enqueue an orchestrator context for async processing.
        Non-blocking — returns immediately.
        """
        with self._lock:
            self._queue.append(context)

    def stats(self) -> Dict[str, Any]:
        """Return current learning statistics."""
        with self._lock:
            scores = list(self._scores)
        return {
            "runs": self._run_count,
            "multiplier": self.multiplier,
            "avg_score": sum(scores) / len(scores) if scores else 0.0,
            "baseline": self._baseline,
        }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            batch = []
            with self._lock:
                while self._queue:
                    batch.append(self._queue.popleft())
            for ctx in batch:
                try:
                    self._process(ctx)
                except Exception as exc:
                    logger.error(f"LearningLoop._process failed: {exc}", exc_info=True)
            time.sleep(0.05)

    def _process(self, context: Dict[str, Any]) -> None:
        evaluation = context.get("evaluation") or {}
        overall_score = evaluation.get("overall_score")
        task = context.get("task", "")

        # -- 1. Track performance -----------------------------------------
        with self._lock:
            self._run_count += 1
            run_number = self._run_count
            if overall_score is not None:
                self._scores.append(overall_score)
                if self._baseline is None:
                    self._baseline = max(overall_score, 0.01)
            scores_snapshot = list(self._scores)
            baseline = self._baseline

        if scores_snapshot and baseline:
            avg = sum(scores_snapshot) / len(scores_snapshot)
            self.multiplier = avg / baseline

        # -- 2. Push outcomes into MetaMemoryAgent ------------------------
        if self.meta_memory:
            for entry in context.get("outputs", []):
                agent_name = entry.get("agent", "unknown")
                if entry.get("output"):
                    try:
                        self.meta_memory.log_event(
                            event_type="agent_outcome",
                            payload={
                                "agent_name": agent_name,
                                "task": task,
                                "score": overall_score,
                                "run": run_number,
                                "status": entry.get("status"),
                            },
                            tags=["outcome", agent_name],
                        )
                    except Exception as exc:
                        logger.debug(f"LearningLoop: meta_memory.log_event failed: {exc}")

        # -- 3. Nudge DynamicConfigManager based on rolling trend ----------
        if self.config_manager and len(scores_snapshot) >= 5:
            avg = sum(scores_snapshot) / len(scores_snapshot)
            try:
                if avg < 0.45:
                    # System underperforming: be more conservative
                    current_retries = self.config_manager.get_parameter("max_retries")
                    if current_retries is not None and current_retries > 1:
                        self.config_manager.set_parameter(
                            "max_retries",
                            current_retries - 1,
                            reason=f"learning_loop avg_score={avg:.3f} < 0.45",
                        )
                    current_timeout = self.config_manager.get_parameter("timeout_seconds")
                    if current_timeout is not None and current_timeout > 30:
                        self.config_manager.set_parameter(
                            "timeout_seconds",
                            max(30, current_timeout - 5),
                            reason=f"learning_loop avg_score={avg:.3f}",
                        )
                elif avg > 0.80:
                    # System performing well: scale up throughput
                    current_batch = self.config_manager.get_parameter("batch_size")
                    if current_batch is not None:
                        self.config_manager.set_parameter(
                            "batch_size",
                            min(50, current_batch + 5),
                            reason=f"learning_loop avg_score={avg:.3f} > 0.80",
                        )
            except Exception as exc:
                logger.debug(f"LearningLoop: config_manager update failed: {exc}")

        # -- 4. Trigger MetaEvolverAgent every N runs ---------------------
        if self.meta_evolver and run_number % self.evolve_every == 0:
            try:
                self.meta_evolver.evolve([], context)
                logger.info(
                    f"LearningLoop: MetaEvolver triggered at run {run_number} "
                    f"(multiplier={self.multiplier:.3f}x)"
                )
            except Exception as exc:
                logger.error(f"LearningLoop: MetaEvolver.evolve failed: {exc}")

        # -- 5. Periodic status log ----------------------------------------
        if run_number % 10 == 0 and scores_snapshot:
            avg = sum(scores_snapshot) / len(scores_snapshot)
            logger.info(
                f"LearningLoop run={run_number} "
                f"avg_score={avg:.3f} multiplier={self.multiplier:.3f}x"
            )


# Module-level singleton ---------------------------------------------------

_loop_instance: Optional[LearningLoop] = None
_loop_lock = threading.Lock()


def get_learning_loop() -> Optional[LearningLoop]:
    """Return the running LearningLoop singleton, or None if not started."""
    return _loop_instance


def init_learning_loop(
    meta_memory=None,
    config_manager=None,
    meta_evolver=None,
    evolve_every: int = 5,
) -> LearningLoop:
    """Create (if needed) and start the LearningLoop singleton."""
    global _loop_instance
    with _loop_lock:
        if _loop_instance is None:
            _loop_instance = LearningLoop(
                meta_memory=meta_memory,
                config_manager=config_manager,
                meta_evolver=meta_evolver,
                evolve_every=evolve_every,
            )
            _loop_instance.start()
    return _loop_instance
