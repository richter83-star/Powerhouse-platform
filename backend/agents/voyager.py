class Agent:
    CAPABILITIES = ["planning", "tool_use", "generation"]

    def run(self, context):
        return "voyager processed: " + context.get('task','')

    def reflect(self, context):
        task = context.get("task", "")
        lesson = "Chart exploration steps before execution."
        return f"Reflection: Voyager processed '{task}'. Lesson learned: {lesson}"
