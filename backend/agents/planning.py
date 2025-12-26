class Agent:
    def run(self, context):
        return "planning processed: " + context.get('task','')

    def reflect(self, context):
        task = context.get("task", "")
        lesson = "Clarify constraints before expanding the plan."
        return f"Reflection: Planning completed for '{task}'. Lesson learned: {lesson}"
