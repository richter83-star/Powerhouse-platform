class Agent:
    def run(self, context):
        return "voyager processed: " + context.get('task','')
