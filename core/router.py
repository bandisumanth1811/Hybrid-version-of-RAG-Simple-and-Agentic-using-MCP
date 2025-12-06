class Router:
    def __init__(self):
        self.simple_keywords = ["how", "guide", "policy", "tutorial", "what is"]
        self.agentic_keywords = ["where", "code", "who", "blame", "class", "function", "bug", "fix", "impl", "line"]

    def route(self, query: str) -> str:
        """
        Decides whether to use 'simple' or 'agentic' strategy.
        """
        q = query.lower()
        
        # Check agentic first (more specific)
        for kw in self.agentic_keywords:
            if kw in q:
                return "agentic"
                
        # Default to simple for general questions
        for kw in self.simple_keywords:
            if kw in q:
                return "simple"
                
        # Fallback
        return "simple"
