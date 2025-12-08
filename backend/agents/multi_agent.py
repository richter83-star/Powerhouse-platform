class Agent:
    def run(self, context):
        return "multi_agent processed: " + context.get('task','')
