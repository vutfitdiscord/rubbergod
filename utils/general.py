import math
import re
import time
from datetime import datetime, timezone, tzinfo
from typing import Callable

import disnake
from dateutil import parser
from dateutil.parser import ParserError
from dateutil.relativedelta import relativedelta
from disnake import Emoji, PartialEmoji
from disnake.ext import commands
from sqlalchemy.schema import Table

from config.app_config import config
from config.messages import Messages
from database import cooldown, session
from permissions.custom_errors import InvalidTime
from rubbergod import Rubbergod
from utils.constants import MAX_ATTACHMENT_SIZE


def id_to_datetime(snowflake_id: int) -> datetime:
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


def cut_string(string: str, part_len: int) -> list:
    return list(string[0 + i : part_len + i] for i in range(0, len(string), part_len))


def split_to_parts(items: list, size: int) -> list:
    """Splits list into smaller lists with given size"""
    result = []

    for x in range(math.ceil(len(items) / size)):
        result.append(items[x * size : (x * size) + size])

    return result


def cut_string_by_words(string: str, part_len: int, delimiter: str) -> list:
    """returns list of strings with length of part_len, only whole words"""
    result = []
    while True:
        if len(string) < part_len:
            result.append(string)
            break
        chunk = string[:part_len]
        last_delimiter = chunk.rindex(delimiter)  # get index of last delimiter
        chunk = chunk[:last_delimiter]
        result.append(chunk)
        string = string[len(chunk) :]
    return result


def split(array: list, k: int) -> list:
    """Splits list into K parts of approximate equal length"""
    n = len(array)
    lists = [array[i * (n // k) + min(i, n % k) : (i + 1) * (n // k) + min(i + 1, n % k)] for i in range(k)]
    return lists


def get_emoji(guild: disnake.Guild, name: str) -> disnake.Emoji | None:
    """
    guild: :class:`disnake.Guild`

    name: :class:`str`
    returns: :class:`disnake.Emoji` or None
    """
    return disnake.utils.get(guild.emojis, name=name)


def clear_link_escape(link: str) -> str:
    """Removes < and > escapes from link."""

    if link.startswith("<"):
        link = link[1:]
    if link.endswith(">"):
        link = link[:-1]

    return link


def make_pts_column_row_formatter(pts_column_name: str) -> Callable[[Table], str]:
    """For leaderboards with one column of points."""

    def formatter(entry: Table, **kwargs):
        return Messages.base_leaderboard_format_str.format_map(kwargs) + " {} pts".format(
            getattr(entry, pts_column_name)
        )

    return formatter


def create_bar(value: int, total: int) -> str:
    """
    creates progress bar
    returns string like this: ▓▓▓▓▓░░░░░ 50%
    """
    prog_bar_str = ""
    prog_bar_length = 10
    percentage = 0.0
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

    async def check_cooldown(self, inter: disnake.ApplicationCommandInteraction) -> bool:
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


def get_command_id(bot: Rubbergod, name: str) -> int | None:
    """get slash command ID by name"""
    command = bot.get_global_command_named(name)
    if command is None:
        guild = bot.get_guild(config.guild_id)
        command = guild.get_command_named(name)
    return getattr(command, "id", None)


async def get_or_fetch_channel(bot: Rubbergod, channel_id: int) -> disnake.TextChannel:
    channel: disnake.TextChannel = bot.get_channel(channel_id)
    if channel is None:
        channel = await bot.fetch_channel(channel_id)
    return channel


async def parse_attachments(
    message: disnake.Message,
    limit: int = MAX_ATTACHMENT_SIZE,
) -> tuple[list[disnake.File], list[disnake.File], list[disnake.Attachment]]:
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
        if attachment.size > limit:
            attachments_too_big.append(attachment)
            continue

        if "image" in attachment.content_type:
            images.append(await attachment.to_file())
        else:
            files.append(await attachment.to_file())

    return images, files, attachments_too_big


def get_local_zone() -> tzinfo | None:
    """Return local timezone"""
    return datetime.now().astimezone().tzinfo


def parse_time(time_string: str, time_format: str) -> datetime | None:
    """Parse local time from string to datetime object.
    Using first regex for abbreviations and if it fails, use dateutil parser.

    Returns
    -------
    datetime object in UTC
    """
    options = ["forever", "never", "nikdy", "none"]
    if time_string.lower() in options:
        return datetime(9999, 12, 30, 0, 0, 0, tzinfo=timezone.utc)

    pattern = re.compile(r"(\d+)([yYMwdhms])")
    matches = pattern.findall(time_string)

    if matches:
        time = datetime.now(timezone.utc)
        timedelta = None
        while matches:
            match = matches.pop()
            value, unit = match
            if unit.lower() in ["y", "r"]:
                timedelta = relativedelta(years=int(value))
            elif unit == "M":
                timedelta = relativedelta(months=int(value))
            elif unit == "w":
                timedelta = relativedelta(weeks=int(value))
            elif unit == "d":
                timedelta = relativedelta(days=int(value))
            elif unit == "h":
                timedelta = relativedelta(hours=int(value))
            elif unit == "m":
                timedelta = relativedelta(minutes=int(value))
            elif unit == "s":
                timedelta = relativedelta(seconds=int(value))
            try:
                time = time + timedelta
            except ValueError:
                raise InvalidTime(time_format)
    else:
        try:
            time = parser.parse(time_string, dayfirst=True)
            time = time.astimezone(get_local_zone())
        except ParserError:
            raise InvalidTime(time_format)

    return time.astimezone(timezone.utc)


async def get_message_from_url(bot: Rubbergod, message_url: str) -> disnake.Message | None:
    link = message_url.split("/")
    msg_id = int(link[-1])
    channel_id = int(link[-2])
    guild_id = int(link[-3])

    try:
        guild = bot.get_guild(guild_id)
        channel = guild.get_channel_or_thread(channel_id)
        message = await channel.fetch_message(msg_id)
        return message
    except disnake.NotFound:
        return None
