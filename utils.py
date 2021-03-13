from datetime import datetime, timezone
from typing import Iterable, Optional, Union

import discord
import math
from discord import Member, PartialEmoji, Emoji
from discord.ext import commands

from config.app_config import Config
from config.messages import Messages


def generate_mention(user_id):
    return f"<@{user_id}>"


def id_to_datetime(snowflake_id: int):
    return datetime.fromtimestamp(((snowflake_id >> 22) + 1420070400000) / 1000)


def str_emoji_id(emoji):
    if isinstance(emoji, int):
        return str(emoji)
    if isinstance(emoji, str):
        return emoji
    if isinstance(emoji, PartialEmoji) or isinstance(emoji, Emoji):
        if emoji.id is None:
            return emoji.name
        else:
            return str(emoji.id)

    return None


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
    if "user" in kwargs:
        kwargs["user"] = generate_mention(kwargs["user"])

    if "admin" in kwargs:
        kwargs["admin"] = generate_mention(kwargs["admin"])

    to_escape = ["role", "not_role", "line"]

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
    elif emoji == "⏩":
        next_page = max_page
    if 1 <= next_page <= max_page:
        return next_page
    else:
        return 0


def is_bot_admin(ctx: commands.Context):
    return ctx.author.id in Config.admin_ids


def cut_string(string: str, part_len: int):
    return list(string[0 + i: part_len + i] for i in range(0, len(string), part_len))


def split_to_parts(items, size: int):
    result = []

    for x in range(math.ceil(len(items) / size)):
        result.append(items[x * size:(x * size) + size])

    return result


class NotHelperPlusError(commands.CommandError):
    """An error indicating that a user doesn't have permissions to use
    a command that is available only to helpers, submods and mods.
    """


def helper_plus(ctx):
    allowed_roles = {Config.mod_role, Config.submod_role, Config.helper_role}
    for role in ctx.author.roles:
        if role.id in allowed_roles:
            return True
    if ctx.author.id in Config.admin_ids:
        return True
    raise NotHelperPlusError


def add_author_footer(embed: discord.Embed, author: discord.User,
                      set_timestamp=True, additional_text: Iterable[str] = []):
    """
    Adds footer to the embed with author name and icon from ctx.

    :param author: author info
    :param embed: discord.Embed object
    :param set_timestamp: bool, should the embed's timestamp be set
    :param additional_text: Iterable of strings that will be joined with author name by pipe symbol, eg.:
    "john#2121 | text1 | text2".
    """

    if set_timestamp:
        embed.timestamp = datetime.now(tz=timezone.utc)

    embed.set_footer(icon_url=author.avatar_url, text=' | '.join((str(author), *additional_text)))


def get_emoji(guild: discord.Guild, name: str) -> Optional[discord.Emoji]:
    """
    guild: :class:`discord.Guild`

    name: :class:`str`
    returns: :class:`discord.Emoji` or None
    """
    return discord.utils.get(guild.emojis, name=name)


def get_username(user: Union[discord.User, discord.Member]) -> str:
    return discord.utils.escape_markdown(user.display_name).replace("@", "@ ")


def get_command_group_signature(ctx: commands.Context):
    """Return signature of group command
    `?group [subcommand1, subcommand2]`
    """
    subcommands = [subcommand.name for subcommand in ctx.command.commands]
    return f"`{ctx.prefix}{ctx.command.name} [{', '.join(subcommands)}]`"


def get_command_signature(ctx: commands.Context):
    """Return signature of command in group
    `?(group sub)command [args]`
    """
    return f"{ctx.prefix}{ctx.command} {ctx.command.signature}"


def clear_link_escape(link: str):
    """Removes < and > escapes from link."""

    if (link.startswith("<")):
        link = link[1:]
    if (link.endswith(">")):
        link = link[:-1]

    return link


async def add_pagination_reactions(message: discord.Message, items_count: int):
    """Common method to add pagination reactions to message."""

    if items_count <= 1:
        return

    if items_count > 2:
        await message.add_reaction("⏪")

    await message.add_reaction("◀")
    await message.add_reaction("▶")

    if items_count > 2:
        await message.add_reaction("⏩")


def is_valid_datetime_format(dt: str, fmt: str) -> bool:
    """Checks if string have valid datetime format"""

    try:
        datetime.strptime(dt, fmt)
        return True
    except ValueError:
        return False


def is_command_message(cmd: str, msg: str, require_space=True) -> bool:
    """Checks whether the message starts with a specified command"""
    cmd = cmd.strip()
    msg_len = len(msg)

    for prefix in Config.command_prefix:
        cmd_p = f"{prefix}{cmd}"
        cmd_p_len = len(cmd_p)

        if msg.find(cmd_p) == 0:
            if require_space:
                return msg_len > cmd_p_len and msg[cmd_p_len].isspace()
            else:
                return True

    return False
