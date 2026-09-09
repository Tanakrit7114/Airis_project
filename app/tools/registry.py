class ToolRegistry:
    def __init__(self):
        self.tools={}; self.metadata={}
    def register(self,name,tool,description=""):
        self.tools[name]=tool; self.metadata[name]={"description":description}
    def get(self,name): return self.tools.get(name)
    def describe(self): return [{"name":n,**self.metadata.get(n,{})} for n in self.tools]
