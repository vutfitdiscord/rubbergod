import math
import os
import re
import time
from datetime import datetime, timezone
from typing import Callable, Iterable, List, Literal, Optional, Tuple, Union

import disnake
from disnake import Emoji, Member, PartialEmoji
from disnake.ext import commands
from genericpath import isfile
from sqlalchemy.schema import Table

from config.app_config import config
from config.messages import Messages
from database import cooldown, session


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


def cut_string(string: str, part_len: int) -> list:
    return list(string[0 + i: part_len + i] for i in range(0, len(string), part_len))


def split_to_parts(items, size: int) -> list:
    """Splits list into smaller lists with given size"""
    result = []

    for x in range(math.ceil(len(items) / size)):
        result.append(items[x * size:(x * size) + size])

    return result


def cut_string_by_words(string: str, part_len: int, delimiter: str) -> list:
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


def split(array, k) -> list:
    """Splits list into K parts of approximate equal length"""
    n = len(array)
    lists = [array[i * (n // k) + min(i, n % k):(i+1) * (n // k) + min(i+1, n % k)] for i in range(k)]
    return lists


def add_author_footer(
    embed: disnake.Embed,
    author: disnake.User,
    set_timestamp=True,
    additional_text: Iterable[str] = [],
    anonymous: bool = False
):
    """
    Adds footer to the embed with author name and icon from ctx.

    :param author: author info
    :param embed: disnake.Embed object
    :param set_timestamp: bool, should the embed's timestamp be set
    :param additional_text: Iterable of strings that will be joined with author name by pipe symbol, eg.:
    :param anonymous: bool, show author as Anonymous
    "john#2121 | text1 | text2" or "Anonymous | text1 | text2"
    """

    if set_timestamp:
        embed.timestamp = datetime.now(tz=timezone.utc)

    if anonymous:
        display_name = "Anonymous"
        display_avatar = author.default_avatar.url
    else:
        display_name = author
        display_avatar = author.display_avatar.url

    embed.set_footer(icon_url=display_avatar, text=' | '.join((str(display_name), *additional_text)))


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
    ignored = ["__init__.py", "base.py"]
    cog_pattern = re.compile(r"class\s+(\w+)\((?:\w+,\s)*commands\.Cog")

    for name in os.listdir("./cogs"):
        filepath = f"./cogs/{name}"

        # ignore __init__.py, non-python files and folders/non-existent files
        if name in ignored or not name.endswith(".py") or not isfile(filepath):
            continue

        # get all cog classes
        with open(os.path.join("./cogs", name), "r") as file:
            contents = file.read()
            match = cog_pattern.findall(contents)
            if match:
                all_cogs[match[0].lower()] = match[0]

    all_cogs = {key: all_cogs[key] for key in sorted(all_cogs.keys())}
    return all_cogs


def create_bar(value, total) -> str:
    """
    creates progress bar
    returns string like this: ▓▓▓▓▓░░░░░ 50%
    """
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


class PCommandOnCooldown(commands.CommandError):
    """commands.CommandOnCooldown requires usage of disnake for cooldowns, so we use a custom exception"""

    pass


class PersistentCooldown:
    def __init__(self, command_name: str, limit: float) -> None:
        self.command_name = command_name
        self.limit = limit * 1000  # convert to ms

    async def check_cooldown(self, inter: disnake.ApplicationCommandInteraction) -> None:
        current_cooldown = session.query(cooldown.CooldownDB).get(
            dict(command_name=self.command_name, user_id=str(inter.user.id))
        )
        now = int(time.time() * 1000)
        if current_cooldown is None:
            session.add(
                cooldown.CooldownDB(
                    command_name=self.command_name,
                    user_id=str(inter.user.id),
                    timestamp=now,
                )
            )
        elif (time_passed := now - current_cooldown.timestamp) < self.limit:
            raise PCommandOnCooldown(Messages.cooldown(time=(self.limit - time_passed) / 1000))
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


async def get_users_from_tag(self, tag):
    """get user(s) object(s) from tag(s), return list of user(s)"""
    users = []
    # regex to match global name or nickname
    user_ids = re.findall(r'<@[!]?\d+>', tag)
    for user in user_ids:
        user = re.search(r'\d+', user)
        user = await self.bot.get_or_fetch_user(int(user.group()))
        users.append(user)
    return users


async def get_members_from_tag(guild, tag):
    """get member(s) object(s) from tag(s), return list of member(s)"""
    members = []
    # regex to match global name or nickname
    member_ids = re.findall(r'<@[!]?\d+>', tag)
    for member in member_ids:
        member = re.search(r'\d+', member)
        member = await guild.get_or_fetch_member(int(member.group()))
        if member is None:
            continue
        members.append(member)
    return members


def get_local_zone():
    return datetime.now().astimezone().tzinfo


time_types = Literal["Default", "Short Time", "Long Time", "Short Date", "Long Date",
                     "Short Date/Time", "Long Date/Time", "Relative Time"]


time_types_dict = {
    "Default": "",
    "Short Time": ":t",
    "Long Time": ":T",
    "Short Date": ":d",
    "Long Date": ":D",
    "Short Date/Time": ":f",
    "Long Date/Time": ":F",
    "Relative Time": ":R"
}


def get_discord_timestamp(dt: datetime, style: time_types = "Default") -> str:
    """get unix timestamp from datetime object and return it as discord timestamp
    more about discord timestamps: https://gist.github.com/LeviSnoot/d9147767abeef2f770e9ddcd91eb85aa

    Default and Short Date/Time formats are identical, but for the sake of consistency,
    I've left them as separate options.

    returns
    -------
    <t:unix_time[:type]>
    """
    if style not in time_types_dict:
        raise ValueError(f"Invalid timestamp style: {style}")
    return f"<t:{int(dt.timestamp())}{time_types_dict[style]}>"


async def get_or_fetch_channel(bot, channel_id) -> disnake.TextChannel:
    channel: disnake.TextChannel = bot.get_channel(channel_id)
    if channel is None:
        channel: disnake.TextChannel = await bot.fetch_channel(channel_id)
    return channel


async def parse_attachments(
    message: disnake.Message
) -> Tuple[List[disnake.File], List[disnake.File], List[disnake.Attachment]]:
    """Parse attachments from message and return them as lists of disnake files
    and if they are over 25MB as attachments.

    Returns
    -------
    Returns three lists containing disnake files or attachments.
    - first list contains images
    - second list contains files
    - third list contains attachments that are over 25MB and can't be uploaded
    """

    images = []
    files = []
    attachments_too_big = []

    if not message.attachments:
        return [], [], []

    for attachment in message.attachments:
        if attachment.size > 25000000:      # 25MB
            attachments_too_big.append(attachment)
            continue

        if "image" in attachment.content_type:
            images.append(await attachment.to_file())
        else:
            files.append(await attachment.to_file())

    return images, files, attachments_too_big
