class SingletonMeta(type):
    _instances = {}

    @staticmethod
    def indentify(cls, *args, **kwargs) -> str:
        return str(id(cls))

    def __call__(cls, *args, **kwargs):
        identification = cls.indentify(cls, *args, **kwargs)
        if identification not in cls._instances:
            cls._instances[identification] = super().__call__(*args, **kwargs)
        return cls._instances[identification]
