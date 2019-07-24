import git


def generate_mention(user_id):
    return '<@' + str(user_id) + '>'


def git_hash():
    repo = git.Repo(search_parent_directories=True)
    return repo.head.object.hexsha


def git_commit_msg():
    repo = git.Repo(search_parent_directories=True)
    return repo.head.commit.message


def str_emoji_id(emoji):
    if isinstance(emoji, int):
        return str(emoji)

    return emoji if isinstance(emoji, str) else emoji.id


def has_role(user, role_name: str):
    return role_name.lower() in [x.name.lower() for x in user.roles]