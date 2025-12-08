class Agent:
    def run(self, context):
        return "react processed: " + context.get('task', '')
