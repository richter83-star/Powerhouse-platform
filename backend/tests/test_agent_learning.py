import asyncio
from datetime import datetime, timedelta

from core.base_agent import BaseAgent
from core.autonomous_goal_executor import AutonomousGoalExecutor
from core.proactive_goal_setter import Goal, GoalType, GoalPriority
from agents.memory_agent import MetaMemoryAgent
from agents.evaluator_agent import EvaluatorAgent


class DummyGoalAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="dummy_goal_agent",
            agent_type="test",
            capabilities=["reflection"]
        )

    def execute(self, input_data, context):
        task = input_data.get("task", "")
        return {"status": "success", "output": f"Handled goal task: {task}", "metadata": {}}

    def reflect(self, context):
        return "Reflection: dummy agent executed. Lesson learned: stay aligned with goal intent."


def test_agent_learning_cycle():
    memory = MetaMemoryAgent()
    evaluator = EvaluatorAgent()
    executor = AutonomousGoalExecutor(
        {
            "meta_memory_agent": memory,
            "evaluator": evaluator,
            "action_delay_seconds": 0
        }
    )

    dummy_agent = DummyGoalAgent()

    def handler(params, goal_id):
        result = dummy_agent.execute({"task": params.get("goal_id", "")}, {"goal_id": goal_id})
        return {"success": True, "output": result["output"], "agent_instance": dummy_agent}

    executor.register_action_handler("test_action", handler)

    memory.add_memory("How to approach goal: Improve latency", tags=["seed"])

    goal = Goal(
        goal_id="goal-123",
        goal_type=GoalType.PERFORMANCE_TARGET,
        priority=GoalPriority.MEDIUM,
        description="Improve latency",
        target_metric="latency",
        current_value=200.0,
        target_value=150.0,
        deadline=datetime.now() + timedelta(hours=1),
        actions=["test_action"]
    )

    plan = executor.create_execution_plan(goal)
    result = asyncio.run(executor._execute_goal(plan))

    assert result.reflection
    assert result.evaluation
    assert result.memory_entry_id

    retrieved = memory.retrieve("How to approach goal: Improve latency", top_k=1, min_score=0.0)
    assert retrieved

    stored_evaluations = [m for m in memory.memory_store if m.get("evaluation")]
    assert stored_evaluations
