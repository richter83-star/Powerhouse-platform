class Agent:
    def run(self, context):
        return "debate processed: " + context.get('task', '')

    def reflect(self, context):
        task = context.get("task", "")
        lesson = "Surface counterarguments before committing."
        return f"Reflection: Debate agent processed '{task}'. Lesson learned: {lesson}"
