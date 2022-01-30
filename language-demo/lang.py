import importlib


class Language:
    def __init__(self, lang):
        module = importlib.import_module(f'languages.{lang}')
        self.__dict__.update(module.__dict__)

    def __getattr__(self, name):
        return self.__dict__.get(name, name)
