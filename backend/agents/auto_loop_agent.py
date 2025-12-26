class Agent:
    def run(self, context):
        return "auto_loop_agent processed: " + context.get('task','')

    def reflect(self, context):
        task = context.get("task", "")
        lesson = "Avoid unnecessary loops; exit early when goal is met."
        return f"Reflection: AutoLoop handled '{task}'. Lesson learned: {lesson}"
