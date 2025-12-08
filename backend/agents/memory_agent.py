class Agent:
    def run(self, context):
        return "memory_agent processed: " + context.get('task','')
