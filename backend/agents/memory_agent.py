from base_agent import BaseAgent
from typing import List, Dict, Any, Optional
from utils.logging import get_logger
import time
import uuid

import numpy as np
from sentence_transformers import SentenceTransformer, util

logger = get_logger(__name__)


class MetaMemoryAgent(BaseAgent):
    """
    A meta-level agent that evaluates, scores, compresses, and manages memory across agents.
    """

    def __init__(
        self,
        embedding_model: str = "all-MiniLM-L6-v2",
        memory_limit: int = 1000,
        decay_half_life: float = 3600.0,  # 1 hour
    ):
        super().__init__()
        self.model = SentenceTransformer(embedding_model)
        self.memory_store: List[Dict[str, Any]] = []
        self.memory_limit = memory_limit
        self.decay_half_life = decay_half_life
        self.embedding_cache: Dict[str, np.ndarray] = {}

    def add_memory(self, content: str, tags: Optional[List[str]] = None) -> str:
        """
        Add a new memory entry with content and optional tags.
        """
        memory_id = str(uuid.uuid4())
        embedding = self._embed(content)
        self.memory_store.append({
            "id": memory_id,
            "content": content,
            "embedding": embedding,
            "tags": tags or [],
            "timestamp": time.time(),
            "relevance": 1.0
        })
        logger.debug(f"Memory added: {memory_id}")
        return memory_id

    def execute(self, context: Dict[str, Any]) -> str:
        """
        Run the memory pruning, scoring, and compression routine.
        """
        logger.info("MetaMemoryAgent executing memory optimization...")

        task = context.get("task", "")
        task_embedding = self._embed(task)

        for memory in self.memory_store:
            decay = self._temporal_decay(memory["timestamp"])
            similarity = float(util.cos_sim(memory["embedding"], task_embedding)[0])
            memory["relevance"] = similarity * decay

        # Optional: Summarize low-relevance clusters
        self._compress_low_relevance_memories()

        # Prune least relevant
        self.memory_store.sort(key=lambda m: m["relevance"], reverse=True)
        self.memory_store = self.memory_store[:self.memory_limit]

        logger.info(f"Memory pruned to {len(self.memory_store)} items.")
        return "Memory optimized and pruned."

    def retrieve(self, query: str, top_k: int = 5, min_score: float = 0.4) -> List[Dict[str, Any]]:
        """
        Retrieve top-k most relevant memories to a query.
        """
        query_embedding = self._embed(query)
        results = []
        for m in self.memory_store:
            sim = float(util.cos_sim(query_embedding, m["embedding"])[0])
            if sim >= min_score:
                results.append({**m, "score": sim})

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def _temporal_decay(self, timestamp: float) -> float:
        """
        Exponential decay function over time.
        """
        age = time.time() - timestamp
        return 0.5 ** (age / self.decay_half_life)

    def _embed(self, text: str) -> np.ndarray:
        """
        Embed a string with caching.
        """
        if text in self.embedding_cache:
            return self.embedding_cache[text]
        emb = self.model.encode(text, convert_to_tensor=True)
        self.embedding_cache[text] = emb
        return emb

    def _compress_low_relevance_memories(self, threshold: float = 0.2):
        """
        Merge and summarize low-relevance memories.
        """
        low_memories = [m for m in self.memory_store if m["relevance"] < threshold]
        if len(low_memories) < 3:
            return  # Too few to summarize

        combined_text = " ".join(m["content"] for m in low_memories)
        summary = f"Summary of {len(low_memories)} past events: {combined_text[:300]}..."  # Replace with LLM summary

        self.memory_store = [m for m in self.memory_store if m["relevance"] >= threshold]
        self.add_memory(content=summary, tags=["compressed", "summary"])
