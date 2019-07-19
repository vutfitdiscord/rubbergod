import git


class Utils:

    @staticmethod
    def generate_mention(user_id):
        return '<@' + str(user_id) + '>'

    @staticmethod
    def git_hash():
        repo = git.Repo(search_parent_directories=True)
        return repo.head.object.hexsha
