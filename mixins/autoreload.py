import weakref
import importlib
import os.path

"""
    Works by overwriting existing class instances with data from
    a newly constructed instance
"""


class AutoReload:
    _instances = dict()
    _modules = dict()

    def __init__(self, name):
        cls = self.__class__

        # No instance of class yet created, instantiate list and import module
        if cls not in self._instances:
            self._instances[cls] = []
            self._modules[cls] = importlib.import_module(name)

        self._instances[cls].append(weakref.ref(self))

    def __del__(self):
        self._instances[self.__class__].remove(weakref.ref(self))

    @classmethod
    def reload(cls, path):
        for module_class in cls._modules.copy():
            module = cls._modules[module_class]
            if module.__file__ == path:
                print("Reloading class {}".format(module_class.__name__))
                cls._reload_class(module_class)

    @classmethod
    def _reload_class(cls, reloaded_class):
        instances = cls._instances[reloaded_class]
        if len(instances) > 0:
            module = importlib.reload(cls._modules[reloaded_class])

            # Create a new object instance and rewrite old instance
            new_instance = getattr(module, reloaded_class.__name__)()
            new_class = new_instance.__class__

            for instance in instances:
                instance().__dict__ = new_instance.__dict__.copy()
                instance().__class__ = new_class

            del new_instance

            # Move instance list from old class to new class, update _modules
            cls._instances[new_class] = cls._instances.pop(reloaded_class)
            cls._modules[new_class] = module
            cls._modules.pop(reloaded_class)
