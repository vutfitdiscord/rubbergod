import disnake
from utils import generate_mention

class CallableString(str):
    to_escape = ["role", "not_role", "line"]

    def __call__(self, *args, **kwargs):
        if "user" in kwargs:
            kwargs["user"] = generate_mention(kwargs["user"])

        if "admin" in kwargs:
            kwargs["admin"] = generate_mention(kwargs["admin"])

        for arg in self.to_escape:
            if arg in kwargs:
                kwargs[arg] = disnake.utils.escape_mentions(kwargs[arg])

        return self.format(**kwargs)

class Formatable(type):
    def __init__(cls, clsname, superclasses, attributedict):
        cls.clsname = clsname

    def __getattribute__(cls, key):
        try:
            return CallableString(object.__getattribute__(cls, key))
        except AttributeError:
            raise AttributeError(f"{cls.clsname} class has no attribute {key}")