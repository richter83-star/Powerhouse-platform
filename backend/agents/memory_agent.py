from core.base_agent import BaseAgent
from typing import List, Dict, Any, Optional
from utils.logging import get_logger
import time
import uuid
import json
import os
import re
import hashlib

import numpy as np

try:
    from sentence_transformers import SentenceTransformer, util
    _HAS_SENTENCE_TRANSFORMERS = True
except Exception:
    SentenceTransformer = None
    util = None
    _HAS_SENTENCE_TRANSFORMERS = False

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
        memory_store_path: Optional[str] = None,
    ):
        super().__init__(
            name="MetaMemoryAgent",
            agent_type="memory",
            capabilities=["memory", "reflection", "evaluation", "planning"]
        )
        self._embedder = SentenceTransformer(embedding_model) if _HAS_SENTENCE_TRANSFORMERS else None
        self._fallback_dim = 128
        self.memory_store: List[Dict[str, Any]] = []
        self.memory_limit = memory_limit
        self.decay_half_life = decay_half_life
        self.embedding_cache: Dict[str, np.ndarray] = {}
        self.memory_store_path = memory_store_path or os.getenv("MEMORY_STORE_PATH")
        self._load_from_disk()

    def add_memory(
        self,
        content: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        evaluation: Optional[Dict[str, Any]] = None,
        reflection: Optional[str] = None
    ) -> str:
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
            "relevance": 1.0,
            "metadata": metadata or {},
            "evaluation": evaluation,
            "reflection": reflection
        })
        logger.debug(f"Memory added: {memory_id}")
        self._persist_to_disk()
        return memory_id

    def log_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        tags: Optional[List[str]] = None
    ) -> str:
        content = json.dumps({"event_type": event_type, "payload": payload}, sort_keys=True)
        return self.add_memory(content=content, tags=(tags or []) + [event_type], metadata=payload)

    def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the memory pruning, scoring, and compression routine.
        """
        logger.info("MetaMemoryAgent executing memory optimization...")

        task = context.get("task", "") or input_data.get("task", "")
        task_embedding = self._embed(task)

        for memory in self.memory_store:
            decay = self._temporal_decay(memory["timestamp"])
            similarity = self._similarity(memory["embedding"], task_embedding)
            memory["relevance"] = similarity * decay

        # Optional: Summarize low-relevance clusters
        self._compress_low_relevance_memories()

        # Prune least relevant
        self.memory_store.sort(key=lambda m: m["relevance"], reverse=True)
        self.memory_store = self.memory_store[:self.memory_limit]

        logger.info(f"Memory pruned to {len(self.memory_store)} items.")
        self._persist_to_disk()
        return {
            "status": "success",
            "output": "Memory optimized and pruned.",
            "metadata": {"memory_size": len(self.memory_store)}
        }

    def reflect(self, context: Dict[str, Any]) -> str:
        status = context.get("status") or context.get("result", {}).get("success")
        if status is True:
            lesson = "Memory operations succeeded; keep leveraging recent relevant context."
        else:
            lesson = "Memory operations had issues; tighten query quality and reduce noise."
        return f"Reflection: memory update {'succeeded' if status else 'encountered issues'}. Lesson learned: {lesson}"

    def retrieve(self, query: str, top_k: int = 5, min_score: float = 0.4) -> List[Dict[str, Any]]:
        """
        Retrieve top-k most relevant memories to a query.
        """
        query_embedding = self._embed(query)
        results = []
        for m in self.memory_store:
            sim = self._similarity(query_embedding, m["embedding"])
            if sim >= min_score:
                results.append({**m, "score": sim})

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def get_agent_performance(self) -> Dict[str, float]:
        scores: Dict[str, List[float]] = {}
        for memory in self.memory_store:
            metadata = memory.get("metadata") or {}
            agent_name = metadata.get("agent_name")
            evaluation = memory.get("evaluation") or {}
            score = evaluation.get("overall_score")
            if agent_name and isinstance(score, (int, float)):
                scores.setdefault(agent_name, []).append(float(score))
        return {name: sum(vals) / len(vals) for name, vals in scores.items() if vals}

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
        if not text:
            emb = np.zeros(self._fallback_dim, dtype=float)
            self.embedding_cache[text] = emb
            return emb
        if self._embedder:
            emb = self._embedder.encode(text, convert_to_tensor=False)
            emb = np.array(emb, dtype=float)
        else:
            emb = self._simple_embed(text)
        self.embedding_cache[text] = emb
        return emb

    def _simple_embed(self, text: str) -> np.ndarray:
        tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
        vec = np.zeros(self._fallback_dim, dtype=float)
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
            idx = int(digest[:8], 16) % self._fallback_dim
            vec[idx] += 1.0
        norm = np.linalg.norm(vec)
        return vec / norm if norm else vec

    def _similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        if a is None or b is None:
            return 0.0
        if a.shape != b.shape:
            min_len = min(a.shape[0], b.shape[0])
            a = a[:min_len]
            b = b[:min_len]
        denom = (np.linalg.norm(a) * np.linalg.norm(b))
        return float(np.dot(a, b) / denom) if denom else 0.0

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

    def _load_from_disk(self) -> None:
        if not self.memory_store_path or not os.path.exists(self.memory_store_path):
            return
        try:
            with open(self.memory_store_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            for item in data:
                embedding = np.array(item.get("embedding", []), dtype=float)
                item["embedding"] = embedding
                self.memory_store.append(item)
        except Exception as exc:
            logger.warning(f"Failed to load memory store: {exc}")

    def _persist_to_disk(self) -> None:
        if not self.memory_store_path:
            return
        try:
            data = []
            for item in self.memory_store:
                copy_item = item.copy()
                emb = copy_item.get("embedding")
                if isinstance(emb, np.ndarray):
                    copy_item["embedding"] = emb.tolist()
                data.append(copy_item)
            with open(self.memory_store_path, "w", encoding="utf-8") as handle:
                json.dump(data, handle)
        except Exception as exc:
            logger.warning(f"Failed to persist memory store: {exc}")
