class Agent:
    def run(self, context):
        return "hierarchical_agents processed: " + context.get('task','')

    def reflect(self, context):
        task = context.get("task", "")
        lesson = "Propagate constraints from parent to child agents clearly."
        return f"Reflection: Hierarchical agent handled '{task}'. Lesson learned: {lesson}"
