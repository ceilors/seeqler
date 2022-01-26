class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        identification = id(cls)
        if identification not in cls._instances:
            cls._instances[identification] = super().__call__(*args, **kwargs)
        return cls._instances[identification]
