"""To use one of the converters in a command, you need to import it and use it as a type hint in the command signature."""

from __future__ import annotations

import re
import shlex
from datetime import datetime, timezone

import disnake
from dateutil import parser
from dateutil.parser import ParserError
from dateutil.relativedelta import relativedelta
from disnake.ext import commands

from config.messages import Messages
from permissions.custom_errors import InvalidTime

from .general import get_local_zone


class UsersList:
    """
    Custom converter for users list. Converts string of users into a list of disnake.User.
    Returns object with valid and invalid users.
    """

    def __init__(self) -> None:
        self.input: str = ""  # original string
        self.valid_users: list[disnake.User] = []  # existing users
        self.invalid_users: list[str] = []  # not found users

    @commands.converter_method
    async def convert(cls, inter: disnake.ApplicationCommandInteraction, users_string: str) -> UsersList:
        """Convert a string of users into a list of users objects.
        Try to find the user if not found add them to the invalid users list.

        Parameters
        ----------
        inter: :class:`disnake.ApplicationCommandInteraction`
            The interaction object
        users_string: :class:`str`
            The string of users to convert

        Returns
        -------
        :class: `UsersList`
            The valid and invalid users
        """
        await inter.response.defer(ephemeral=True)

        users_list = UsersList()
        users_list.input = users_string
        split_users = shlex.split(users_string)
        user_converter = commands.UserConverter()

        for user in split_users:
            try:
                users_list.valid_users.append(await user_converter.convert(inter, user))
            except commands.UserNotFound:
                users_list.invalid_users.append(user)

        return users_list


class MembersList:
    """
    Custom converter for members. Converts string of members into a list of disnake.Member.
    Returns valid members, invalid members, valid users and invalid users.
    """

    def __init__(self) -> None:
        self.input: str = ""  # original string
        self.valid_members: list[disnake.Member] = []  # members present in the guild
        self.invalid_members: list[str] = []  # not found members
        self.valid_users: list[disnake.User] = []  # existing users
        self.invalid_users: list[str] = []  # not found users

    @commands.converter_method
    async def convert(cls, inter: disnake.ApplicationCommandInteraction, users_string: str) -> MembersList:
        """Convert a string of users into a list of members.
        Try to find each user as a member. If not found, try to find the user if not found add them to the invalid users list.

        Parameters
        ----------
        inter: :class:`disnake.ApplicationCommandInteraction`
            The interaction object
        users_string: :class:`str`
            The string of users to convert

        Returns
        -------
        :class: `MembersList`
            The found and not found members and users
        """
        await inter.response.defer(ephemeral=True)

        members_list = MembersList()
        members_list.input = users_string

        split_members = shlex.split(users_string)
        member_converter = commands.MemberConverter()
        user_converter = commands.UserConverter()

        for user in split_members:
            try:
                members_list.valid_members.append(await member_converter.convert(inter, user))
            except commands.MemberNotFound:
                members_list.invalid_members.append(user)
                try:
                    members_list.valid_users.append(await user_converter.convert(inter, user))
                except commands.UserNotFound:
                    members_list.invalid_users.append(user)

        return members_list


class DiscordDatetime:
    """
    Custom datetime converter used in commands. Converts string to datetime object.
    """

    def __init__(self) -> None:
        super().__init__()
        self.utc: datetime = datetime.now()
        self.local: datetime = datetime.now()

    @commands.converter_method
    async def convert(cls, _: disnake.ApplicationCommandInteraction, time_string: str) -> DiscordDatetime:
        """Convert local time from string to datetime object.
        Using first regex for abbreviations or if it fails, use dateutil parser.

        Returns
        -------
        :class: `datetime`
            object in UTC
        """

        discord_datetime = DiscordDatetime()

        options = ["forever", "never", "nikdy", "none"]
        if time_string.lower() in options:
            discord_datetime.local = datetime(9999, 12, 30, 0, 0, 0, tzinfo=get_local_zone())
            discord_datetime.utc = datetime(9999, 12, 30, 0, 0, 0, tzinfo=timezone.utc)
            return discord_datetime

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
                    raise InvalidTime(Messages.time_format)
        else:
            try:
                time = parser.parse(time_string, dayfirst=True)
            except ParserError:
                raise InvalidTime(Messages.time_format)

        discord_datetime.local = time.astimezone(get_local_zone())
        discord_datetime.utc = time.astimezone(timezone.utc)
        return discord_datetime
