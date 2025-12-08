class Agent:
    def run(self, context):
        return "reflection processed: " + context.get('task','')
