import importlib
from pathlib import Path


class Language:
    def __init__(self, lang: str):
        module = importlib.import_module(f"resources.lang_{lang.lower()}")
        self.__dict__.update(module.__dict__)

    def __getattr__(self, name):
        return self.__dict__.get(name, name)
