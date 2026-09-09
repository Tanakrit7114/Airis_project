class SecurityPolicy:
    SAFE_ACTIONS = {
        "search",
        "read_memory",
        "read_file",
    }

    def allowed(self, action: str) -> bool:
        return action in self.SAFE_ACTIONS
