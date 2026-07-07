# QUANTAURA Core Engine
import logging
from typing import Dict

class QuantauraEngine:
    def __init__(self):
        self.modules = {}
        self.experiments = []
        logging.basicConfig(level=logging.INFO)

    def load_module(self, name: str, adapter):
        self.modules[name] = adapter
        logging.info(f'Loaded module: {name}')

    def run_experiment(self, module_name: str, params: Dict):
        if module_name in self.modules:
            result = self.modules[module_name].run(params)
            self.experiments.append({'module': module_name, 'params': params, 'result': result})
            return result
        raise ValueError('Module not found')

engine = QuantauraEngine()