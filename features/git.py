import git


class Git:
    def __init__(self):
        self.repo = git.Repo(search_parent_directories=True)
        self.cmd = self.repo.git

    async def pull(self):
        return self.cmd.pull()

    def short_hash(self):
        return self.repo.head.object.hexsha[:7]
