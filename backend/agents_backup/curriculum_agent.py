class Agent:
    def run(self, context: dict) -> str:
        """
        Simple demo agent for curriculum / planning.
        It just echoes the task so the orchestrator pipeline has something to work with.
        """
        task = context.get("task", "")
        return "curriculum_agent processed: " + task
