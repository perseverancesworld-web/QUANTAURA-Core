from typing import Dict, Any

class ModuleRegistry:
    def __init__(self):
        self.modules: Dict[str, Any] = {}

    def register(self, name: str, adapter):
        self.modules[name] = adapter
        print(f'Registered module: {name}')

    def get(self, name: str):
        return self.modules.get(name)

registry = ModuleRegistry()