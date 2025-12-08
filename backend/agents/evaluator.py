class Agent:
    def run(self, context):
        return "evaluator provisional check"
    def evaluate(self, context):
        return {"score": len(context.get("outputs", []))}
