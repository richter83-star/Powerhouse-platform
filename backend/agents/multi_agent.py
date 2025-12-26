class Agent:
    def run(self, context):
        return "multi_agent processed: " + context.get('task','')

    def reflect(self, context):
        task = context.get("task", "")
        lesson = "Coordinate roles early to reduce duplication."
        return f"Reflection: Multi-agent processed '{task}'. Lesson learned: {lesson}"
