class Agent:
    def run(self, context):
        return "auto_loop_agent processed: " + context.get('task','')

