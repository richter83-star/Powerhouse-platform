"""
Generative Agents — persona-based generation with goals and backstory.

Each run instantiates a persona (name, role, backstory, goal) relevant to the
task domain, then generates a response from that persona's perspective.
Multiple personas are consulted and their outputs synthesised, providing
diverse viewpoints on the task.

Inspired by Park et al. (2023) "Generative Agents: Interactive Simulacra of
Human Behavior".
"""

from typing import Dict, Any, List
from config.llm_config import LLMConfig
from utils.logging import get_logger

logger = get_logger(__name__)

# Default personas — the agent selects 2–3 relevant ones per task
_PERSONAS = [
    {
        "name": "Alex",
        "role": "Domain Expert",
        "backstory": "15 years of deep technical expertise; values precision and evidence.",
        "goal": "Provide accurate, well-reasoned technical analysis.",
    },
    {
        "name": "Sam",
        "role": "Creative Strategist",
        "backstory": "Background in product design and lateral thinking; challenges assumptions.",
        "goal": "Generate novel, unconventional approaches to problems.",
    },
    {
        "name": "Jordan",
        "role": "Critical Reviewer",
        "backstory": "Former auditor; known for spotting edge cases and failure modes.",
        "goal": "Identify risks, gaps, and improvements in any proposed solution.",
    },
]


class Agent:
    CAPABILITIES = ["generation", "reasoning", "synthesis", "persona_simulation"]

    def __init__(self):
        self.llm = LLMConfig.get_llm_provider("generative_agents")

    def _invoke(self, prompt: str, max_tokens: int = 500) -> str:
        try:
            result = self.llm.invoke(prompt=prompt, max_tokens=max_tokens)
            return result.strip() if isinstance(result, str) else str(result).strip()
        except Exception as exc:
            logger.warning("GenerativeAgentsAgent LLM call failed: %s", exc)
            return ""

    def run(self, context: Dict[str, Any]) -> str:
        task = context.get("task", "")
        if not task:
            return "Error: no task provided to GenerativeAgentsAgent"

        prior = "\n".join(
            f"- {o['agent']}: {str(o.get('output', ''))[:200]}"
            for o in context.get("outputs", [])[-3:]
            if o.get("status") == "success"
        )

        # Collect each persona's contribution
        contributions: List[str] = []
        for persona in _PERSONAS:
            response = self._invoke(
                f"You are {persona['name']}, a {persona['role']}.\n"
                f"Backstory: {persona['backstory']}\n"
                f"Goal: {persona['goal']}\n\n"
                f"Task: {task}\n"
                + (f"Prior context:\n{prior}\n" if prior else "")
                + f"\nRespond from {persona['name']}'s perspective, in character. "
                "Be concise (3–5 sentences).\n\nResponse:"
            )
            if response:
                contributions.append(f"**{persona['name']} ({persona['role']})**:\n{response}")

        if not contributions:
            return f"GenerativeAgentsAgent: could not generate persona responses for '{task}'"

        # Synthesise into a final answer
        combined = "\n\n".join(contributions)
        synthesis = self._invoke(
            f"Three personas responded to this task: '{task}'\n\n{combined}\n\n"
            "Synthesise their perspectives into one clear, balanced final answer "
            "that captures the best insights from each:\n\nSynthesis:",
            max_tokens=600,
        )

        logger.info("GenerativeAgentsAgent produced %d-persona synthesis", len(contributions))
        return synthesis if synthesis else combined

    def reflect(self, context: Dict[str, Any]) -> str:
        task = context.get("task", "")
        lesson = "Constrain generation to the task domain; diverse personas reduce blind spots."
        return f"Reflection: GenerativeAgentsAgent processed '{task}'. Lesson: {lesson}"
