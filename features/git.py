from discord.ext import commands

import git


class Git():
    def __init__(self):
        self.repo = git.Repo(search_parent_directories=True)
        self.cmd = self.repo.git

    async def pull(self, ctx: commands.Context):
        return self.cmd.pull()
