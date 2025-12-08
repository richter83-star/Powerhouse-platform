class Agent:
    def run(self, context):
        return "debate processed: " + context.get('task', '')
