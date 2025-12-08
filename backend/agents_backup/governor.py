class GovernorAgent:
    skip_in_main = True
    def preflight(self, task: str):
        blocked = any(b in task.lower() for b in ["illegal","malware"])
        if blocked:
            return False, "disallowed content"
        return True, "ok"
