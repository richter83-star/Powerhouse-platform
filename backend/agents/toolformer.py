class Agent:
    def run(self, context):
        return "toolformer processed: " + context.get('task','')

    def reflect(self, context):
        task = context.get("task", "")
        status = context.get("status", "success")
        lesson = "Use tool calls only when they add clear value."
        return f"Reflection: Toolformer {status} on '{task}'. Lesson learned: {lesson}"
