class MetaEvolverAgent:
    skip_in_main = True
    def evolve(self, agents, context):
        agents.sort(key=lambda a: a.__class__.__name__)
        return True
