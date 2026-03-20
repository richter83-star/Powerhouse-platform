"""
Adaptive Memory Agent — semantic short-term memory with relevance-weighted retrieval.

Maintains a bounded in-process memory store. Each update embeds the new
content (using hash-based fingerprints when sentence-transformers is not
available) and stores it with a timestamp. On each run, the most relevant
memories are retrieved and injected into context to help downstream agents.
"""

import hashlib
import time
from collections import deque
from typing import Dict, Any, List, Tuple

from utils.logging import get_logger

logger = get_logger(__name__)

_MAX_MEMORIES = 50
_TOP_K = 5          # memories to surface per run
_DECAY_HALF_LIFE = 3600.0  # seconds — older memories score lower


def _fingerprint(text: str) -> List[float]:
    """Cheap hash-based pseudo-embedding (fallback when sentence-transformers absent)."""
    digest = hashlib.sha256(text.encode()).digest()
    return [b / 255.0 for b in digest[:32]]


def _cosine(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class AdaptiveMemoryAgent:
    CAPABILITIES = ["memory", "analysis", "context_enrichment"]

    def __init__(self):
        self._store: deque = deque(maxlen=_MAX_MEMORIES)  # each entry: (embedding, text, ts)
        self._embed = self._build_embedder()

    def _build_embedder(self):
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("AdaptiveMemoryAgent: using SentenceTransformer embeddings")
            return lambda text: model.encode(text).tolist()
        except Exception:
            logger.debug("AdaptiveMemoryAgent: sentence-transformers unavailable; using hash fingerprint")
            return _fingerprint

    # ------------------------------------------------------------------
    # Public API used by Orchestrator (load / update / run)
    # ------------------------------------------------------------------

    def load(self) -> List[str]:
        """Return the raw text of stored memories (newest first)."""
        return [text for _, text, _ in reversed(list(self._store))]

    def update(self, context: Dict[str, Any], output: Any) -> None:
        """Store a new memory entry from an agent output."""
        text = str(output)[:400]
        if not text.strip():
            return
        emb = self._embed(text)
        self._store.append((emb, text, time.time()))

    def retrieve(self, query: str, top_k: int = _TOP_K) -> List[str]:
        """Return the top-k most relevant (and recent) memories for a query."""
        if not self._store:
            return []
        q_emb = self._embed(query)
        now = time.time()
        scored: List[Tuple[float, str]] = []
        for emb, text, ts in self._store:
            similarity = _cosine(q_emb, emb)
            age_seconds = now - ts
            recency = 2 ** (-age_seconds / _DECAY_HALF_LIFE)
            score = 0.7 * similarity + 0.3 * recency
            scored.append((score, text))
        scored.sort(reverse=True)
        return [text for _, text in scored[:top_k]]

    def run(self, context: Dict[str, Any]) -> str:
        """
        Inject the most relevant memories into the context and return a summary.

        Downstream agents that read ``context["state"]["memory"]`` will see
        the updated list populated by ``load()``.  This method additionally
        surfaces the top-k relevant memories for the current task.
        """
        task = context.get("task", "")
        relevant = self.retrieve(task) if task else self.load()[:_TOP_K]

        if not relevant:
            return f"AdaptiveMemoryAgent: memory store empty (store_size=0)"

        # Inject into context state so subsequent agents can read them
        context.setdefault("state", {})["memory"] = relevant

        summary = "\n".join(f"• {m[:150]}" for m in relevant)
        logger.info(
            "AdaptiveMemoryAgent retrieved %d relevant memories (store_size=%d)",
            len(relevant), len(self._store),
        )
        return f"Memory context ({len(relevant)} items):\n{summary}"

    def reflect(self, context: Dict[str, Any]) -> str:
        return (
            f"Reflection: AdaptiveMemoryAgent — store_size={len(self._store)}. "
            "Lesson: keep memory bounded; prefer recency + relevance weighting."
        )
