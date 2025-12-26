class GovernorAgent:
    skip_in_main = True
    def preflight(self, task: str):
        blocked = any(b in task.lower() for b in ["illegal","malware"])
        if blocked:
            return False, "disallowed content"
        return True, "ok"

    def reflect(self, context):
        task = context.get("task", "")
        lesson = "Block risky content early and provide clear feedback."
        return f"Reflection: Governor reviewed '{task}'. Lesson learned: {lesson}"
