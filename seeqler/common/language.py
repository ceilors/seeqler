from .types import SingletonMeta

import importlib


class Language(metaclass=SingletonMeta):
    def __init__(self, lang: str):
        self.lang = lang
        self.errors = ""

        try:
            module = importlib.import_module(f"resources.lang_{lang.lower()}")
        except ModuleNotFoundError:
            module = importlib.import_module(f"resources.lang_en-us")
            self.errors = f'Language module for "{self.lang}" was not found'
            self.lang = "en-us"

        self.__dict__.update(module.__dict__)

    def __getattr__(self, name):
        # return "$value" if value is not in language module
        # prefix is used to distinguish translation absence clearly
        return self.__dict__.get(name, f"${name}")

    def get(self, name):
        return self.__getattr__(name)
