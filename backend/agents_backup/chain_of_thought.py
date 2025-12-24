class Agent:
    def run(self, context):
        return "chain_of_thought processed: " + context.get('task','')

