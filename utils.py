import git
import discord
from discord import Member
from discord.ext import commands

from config.messages import Messages
from config.config import Config


def generate_mention(user_id):
    return '<@' + str(user_id) + '>'


def git_hash():
    repo = git.Repo(search_parent_directories=True)
    return repo.head.object.hexsha


def git_commit_msg():
    repo = git.Repo(search_parent_directories=True)
    return repo.head.commit.message


def git_pull():
    repo = git.Repo(search_parent_directories=True)
    cmd = repo.git
    return cmd.pull()


def str_emoji_id(emoji):
    if isinstance(emoji, int):
        return str(emoji)

    return emoji if isinstance(emoji, str) else str(emoji.id)


def has_role(user, role_name: str):
    if type(user) != Member:
        return None

    return role_name.lower() in [x.name.lower() for x in user.roles]


def fill_message(message_name, *args, **kwargs):
    """Fills message template from messages by attempting to get the attr.
    :param message_name: {str} message template name
    :kwargs: {dict} data for formatting the template
    :return: filled template
    """

    # Convert username/admin to a mention
    if 'user' in kwargs:
        kwargs['user'] = generate_mention(kwargs['user'])

    if 'admin' in kwargs:
        kwargs['admin'] = generate_mention(kwargs['admin'])

    to_escape = ['role', 'not_role', 'line']

    for arg in to_escape:
        if arg in kwargs:
            kwargs[arg] = discord.utils.escape_mentions(kwargs[arg])

    # Attempt to get message template and fill
    try:
        template = getattr(Messages, message_name)
        return template.format(*args, **kwargs)
    except AttributeError:
        raise ValueError("Invalid template {}".format(message_name))

def pagination_next(emoji, page, max_page):
    if emoji in ["▶", "🔽"]:
        next_page = page + 1
    elif emoji in ["◀", "🔼"]:
        next_page = page - 1
    elif emoji == "⏪":
        next_page = 1
    if 1 <= next_page <= max_page:
        return next_page
    else:
        return 0

def is_bot_owner(ctx: commands.Context):
    return ctx.author.id == Config.admin_id
