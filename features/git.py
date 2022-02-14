import git


class Git():
    def __init__(self):
        self.repo = git.Repo(search_parent_directories=True)
        self.cmd = self.repo.git

    async def pull(self):
        return self.cmd.pull()

    def hash(self):
        return self.repo.head.object.hexsha

    def short_hash(self):
        return self.hash()[:7]

    def last_commit_msg(self):
        return self.repo.head.commit.message
