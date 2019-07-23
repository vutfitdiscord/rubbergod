import weakref


class ConfigBase:
    _instances = []

    def __init__(self):
        self._instances.append(weakref.ref(self))

    def __del__(self):
        self._instances.remove(weakref.ref(self))

    def update(self, conf):
        self.__dict__ = conf.__dict__.copy()

    @classmethod
    def get_instances(cls):
        return cls._instances

    @classmethod
    def set_instances(cls, inst):
        cls._instances = inst

    @classmethod
    def update_all(cls, conf):
        for ref in cls._instances:
            ref().update(conf)
