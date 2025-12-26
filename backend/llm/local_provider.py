"""
Local LLM provider for development and testing without external API keys.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import hashlib
import json

from .base import BaseLLMProvider, LLMResponse
from utils.logging import get_logger

logger = get_logger(__name__)


class LocalLLMProvider(BaseLLMProvider):
    """
    Deterministic, offline LLM provider for smoke tests and local runs.
    """

    def __init__(self, api_key: str = "", default_model: str = "local", **kwargs):
        super().__init__(api_key=api_key, default_model=default_model, **kwargs)
        self.model_name = default_model or "local"
        logger.info("Initialized LocalLLM provider (no external calls).")

    def invoke(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        json_mode: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> LLMResponse:
        content = self._build_response(prompt, system_prompt, json_mode)
        usage = self._estimate_usage(prompt, content)
        return LLMResponse(
            content=content,
            model=model or self.model_name,
            usage=usage,
            finish_reason="stop",
            metadata={"provider": "local", "offline": True},
            timestamp=datetime.now()
        )

    def invoke_streaming(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ):
        content = self._build_response(prompt, system_prompt, json_mode=False)
        chunk_size = 80
        for i in range(0, len(content), chunk_size):
            yield content[i:i + chunk_size]

    def count_tokens(self, text: str, model: Optional[str] = None) -> int:
        return len(text.split())

    def _build_response(
        self,
        prompt: str,
        system_prompt: Optional[str],
        json_mode: bool
    ) -> str:
        prompt_text = " ".join(prompt.split())
        digest = hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()[:8]
        summary = f"Local LLM response ({digest}): {prompt_text[:240]}"

        if json_mode:
            return json.dumps({"response": summary})

        if "FINAL_ANSWER" in prompt and "Action:" in prompt:
            return (
                "Thought: Using local LLM stub for deterministic output.\n"
                "Action: FINAL_ANSWER\n"
                f"Action Input: {summary}"
            )

        return summary

    def _estimate_usage(self, prompt: str, content: str) -> Dict[str, int]:
        prompt_tokens = self.count_tokens(prompt)
        completion_tokens = self.count_tokens(content)
        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens
        }
