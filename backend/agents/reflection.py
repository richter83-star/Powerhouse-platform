class Agent:
    def run(self, context):
        return "reflection processed: " + context.get('task','')

    def reflect(self, context):
        task = context.get("task", "")
        lesson = "Ensure reflection captures both wins and misses."
        return f"Reflection: Reflection agent processed '{task}'. Lesson learned: {lesson}"
