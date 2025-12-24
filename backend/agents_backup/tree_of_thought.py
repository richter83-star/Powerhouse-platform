class Agent:
    def run(self, context):
        return "tree_of_thought processed: " + context.get('task','')

