class Agent:
    def run(self, context):
        return "toolformer processed: " + context.get('task','')
