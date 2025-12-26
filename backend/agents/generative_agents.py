class Agent:
    def run(self, context):
        return "generative_agents processed: " + context.get('task','')

    def reflect(self, context):
        task = context.get("task", "")
        lesson = "Constrain generation to avoid drifting off-task."
        return f"Reflection: Generative agent processed '{task}'. Lesson learned: {lesson}"
