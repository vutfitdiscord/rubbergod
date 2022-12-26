from datetime import datetime, timezone
from typing import Callable, Iterable, Optional, Union
from repository.database import session, cooldown
import time

import disnake
import math
from disnake import Member, PartialEmoji, Emoji
from disnake.ext import commands
from sqlalchemy.schema import Table
import os
import re
from genericpath import isfile
from PIL import Image, ImageDraw

from config.app_config import config
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
            kwargs[arg] = disnake.utils.escape_mentions(kwargs[arg])

    # Attempt to get message template and fill
    try:
        template = getattr(Messages, message_name)
        return template.format(*args, **kwargs)
    except AttributeError:
        raise ValueError("Invalid template {}".format(message_name))


def pagination_next(id: str, page: int, max_page: int, roll_around: bool = True):
    if 'next' in id:
        next_page = page + 1
    elif 'prev' in id:
        next_page = page - 1
    elif 'start' in id:
        next_page = 1
    elif 'end' in id:
        next_page = max_page
    if 1 <= next_page <= max_page:
        return next_page
    elif roll_around and next_page == 0:
        return max_page
    elif roll_around and next_page > max_page:
        return 1
    else:
        return 0


def is_bot_admin(ctx: Union[commands.Context, disnake.ApplicationCommandInteraction]):
    return ctx.author.id in config.admin_ids


def is_bot_admin_or_mod(ctx: Union[commands.Context, disnake.ApplicationCommandInteraction]):
    return ctx.author.id in config.admin_ids or ctx.author.guild_permissions.administrator


def is_in_modroom(ctx: Union[commands.Context, disnake.ApplicationCommandInteraction]):
    return ctx.channel.id == config.mod_room


def cut_string(string: str, part_len: int):
    return list(string[0 + i: part_len + i] for i in range(0, len(string), part_len))


def split_to_parts(items, size: int):
    result = []

    for x in range(math.ceil(len(items) / size)):
        result.append(items[x * size:(x * size) + size])

    return result


def cut_string_by_words(string: str, part_len: int, delimiter: str):
    """returns list of strings with length of part_len, only whole words"""
    result = []
    while True:
        if len(string) < part_len:
            result.append(string)
            break
        chunk = string[:part_len]
        last_delimiter = chunk.rindex(delimiter)    # get index of last delimiter
        chunk = chunk[:last_delimiter]
        result.append(chunk)
        string = string[len(chunk):]
    return result


class NotHelperPlusError(commands.CommandError):
    """An error indicating that a user doesn't have permissions to use
    a command that is available only to helpers, submods and mods.
    """

    pass


def helper_plus(ctx):
    allowed_roles = {config.mod_role, config.submod_role, config.helper_role}
    guild = ctx.bot.get_guild(config.guild_id)
    user = guild.get_member(ctx.author.id)
    for role in user.roles:
        if role.id in allowed_roles:
            return True
    if ctx.author.id in config.admin_ids:
        return True
    raise NotHelperPlusError


def add_author_footer(embed: disnake.Embed, author: disnake.User,
                      set_timestamp=True, additional_text: Iterable[str] = []):
    """
    Adds footer to the embed with author name and icon from ctx.

    :param author: author info
    :param embed: disnake.Embed object
    :param set_timestamp: bool, should the embed's timestamp be set
    :param additional_text: Iterable of strings that will be joined with author name by pipe symbol, eg.:
    "john#2121 | text1 | text2".
    """

    if set_timestamp:
        embed.timestamp = datetime.now(tz=timezone.utc)

    embed.set_footer(icon_url=author.display_avatar.url, text=' | '.join((str(author), *additional_text)))


def get_emoji(guild: disnake.Guild, name: str) -> Optional[disnake.Emoji]:
    """
    guild: :class:`disnake.Guild`

    name: :class:`str`
    returns: :class:`disnake.Emoji` or None
    """
    return disnake.utils.get(guild.emojis, name=name)


def get_username(user: Union[disnake.User, disnake.Member]) -> str:
    return disnake.utils.escape_markdown(user.display_name).replace("@", "@ ")


def get_command_group_signature(ctx: commands.Context):
    """Return signature of group command with checks
    `?group [subcommand1, subcommand2]`
    """
    subcommands = []
    if ctx.command.usage is not None:
        subcommands.append(ctx.command.signature)
    for subcommand in ctx.command.commands:
        for check in subcommand.checks:
            try:
                if not check(ctx):
                    break
            except Exception:
                break
        else:
            subcommands.append(subcommand.name)
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

    for prefix in config.command_prefix:
        cmd_p = f"{prefix}{cmd}"
        cmd_p_len = len(cmd_p)

        if msg.find(cmd_p) == 0:
            if require_space:
                return msg_len > cmd_p_len and msg[cmd_p_len].isspace()
            else:
                return True

    return False


def make_pts_column_row_formatter(pts_column_name: str):
    """For leaderboards with one column of points."""

    def formatter(entry: Table, **kwargs):
        return Messages.base_leaderboard_format_str.format_map(
            kwargs) + " {} pts".format(getattr(entry, pts_column_name))

    return formatter


def get_all_cogs():
    """Returns all available cogs with their class names as ordered dict."""
    all_cogs = {}
    pattern = r"class (.*)\(commands\.Cog\):"
    for name in os.listdir("./cogs"):
        filename = f"./cogs/{name}"
        if isfile(filename) and filename.endswith(".py"):
            with open(filename, "r") as file:
                for line in file:
                    if re.search(pattern, line):
                        result = re.search(pattern, line)
                        all_cogs[name[:-3]] = result.group(1)
                        break
    return {key: all_cogs[key] for key in sorted(all_cogs.keys())}


def split(array, k):
    """Splits list into K parts of approximate equal length"""
    n = len(array)
    lists = [array[i * (n // k) + min(i, n % k):(i+1) * (n // k) + min(i+1, n % k)] for i in range(k)]
    return lists


def create_bar(value, total) -> str:
    prog_bar_str = ""
    prog_bar_length = 10
    percentage = 0
    if total != 0:
        percentage = value / total
        for i in range(prog_bar_length):
            if round(percentage, 1) <= 1 / prog_bar_length * i:
                prog_bar_str += "░"
            else:
                prog_bar_str += "▓"
    else:
        prog_bar_str = "░" * prog_bar_length
    prog_bar_str = prog_bar_str + f" {round(percentage * 100)}%"
    return prog_bar_str


def round_image(frame_avatar: Image.Image) -> Image.Image:
    """Convert square avatar to circle"""
    frame_mask = Image.new("1", frame_avatar.size, 0)
    draw = ImageDraw.Draw(frame_mask)
    draw.ellipse((0, 0) + frame_avatar.size, fill=255)
    frame_avatar.putalpha(frame_mask)
    return frame_avatar


class PCommandOnCooldown(commands.CommandError):
    """commands.CommandOnCooldown requires usage of disnake for cooldowns, so we use a custom exception"""

    pass


class PersistentCooldown:
    def __init__(self, command_name: str, limit: float) -> None:
        self.command_name = command_name
        self.limit = limit * 1000  # convert to ms

    async def check_cooldown(self, inter: disnake.ApplicationCommandInteraction) -> None:
        current_cooldown = session.query(cooldown.Cooldown).get(
            dict(command_name=self.command_name, user_id=str(inter.user.id))
        )
        now = int(time.time() * 1000)
        if current_cooldown is None:
            session.add(
                cooldown.Cooldown(
                    command_name=self.command_name,
                    user_id=str(inter.user.id),
                    timestamp=now,
                )
            )
        elif (time_passed := now - current_cooldown.timestamp) < self.limit:
            raise PCommandOnCooldown(Messages.cooldown.format((self.limit - time_passed) / 1000))
        else:
            current_cooldown.timestamp = now
        session.commit()
        return True

    def __call__(self, f: commands.InvokableApplicationCommand) -> Callable:
        f.add_check(self.check_cooldown)
        return f


def get_command_id(self, name):
    """get slash command ID by name"""
    command = self.bot.get_global_command_named(name)
    if command is None:
        guild = self.bot.get_guild(config.guild_id)
        command = guild.get_command_named(name)
    return getattr(command, "id", None)


async def get_username_from_tag(self, tag):
    """get user name from tag, return list of name(s)"""
    user_names = []
    user_ids = re.findall(r'\d+', tag)
    for user in user_ids:
        user = await self.bot.get_or_fetch_user(int(user))
        user_names.append(user.name)
    return user_names
