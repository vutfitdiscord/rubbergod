import disnake


class CallableString(str):
    to_escape = ["role", "not_role", "line"]
    to_mention = ["user", "admin"]

    def __call__(self, *args, **kwargs):
        for arg in self.to_mention:
            if arg not in kwargs:
                continue

            string = str(kwargs[arg])
            if string.startswith("<@") and string.endswith(">"):
                continue
            kwargs[arg] = f"<@{kwargs[arg]}>"

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
