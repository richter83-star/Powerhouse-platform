class AdaptiveMemoryAgent:
    def __init__(self):
        self.mem = []
    def load(self):
        return self.mem[:]
    def update(self, context, out):
        self.mem.append(out)
    def run(self, context):
        return f"memory_size={len(self.mem)}"
