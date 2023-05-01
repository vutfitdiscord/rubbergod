class Base:
    def __init__(self):
        self.tasks = []

    def cog_unload(self) -> None:
        for task in self.tasks:
            task.cancel()
