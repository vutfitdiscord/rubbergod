"""
Contains functions to check permissions of users, channels and other.
"""

import disnake
from disnake.ext import commands

from config.app_config import config
from config.messages import Messages
from utils.errors import (
    InvalidRoomError,
    PermissionError,
)

PRIVILEGED_ROLES = [config.mod_role, config.submod_role, config.helper_role]


class PermissionsCheck:
    """Class containing methods to check permissions"""

    @classmethod
    def is_bot_admin(
        cls,
        ctx: commands.Context | disnake.ApplicationCommandInteraction = None,
        raise_exception: bool = True,
    ) -> bool:
        """
        Check if the user is a bot admin. Works as a function or a command decorator.

        When `ctx` is passed, it works as a function.
        When `ctx` is not passed, it acts as a decorator for a command.

        Returns
        -------
        bool
            True if user is an admin, False otherwise.
        Exception
            Throws `PermissionError` if `raise_exception=True` and user doesn't have permissions.
        """

        def predicate(ctx: commands.Context | disnake.ApplicationCommandInteraction) -> bool:
            if ctx.author.id in config.admin_ids:
                return True
            if raise_exception:
                raise PermissionError(message=Messages.bot_admin_only)
            return False

        if ctx:
            # If ctx is passed, return the result of the predicate
            return predicate(ctx)
        else:
            # If ctx is not passed, act as a decorator for command
            return commands.check(predicate)

    @classmethod
    def is_mod_plus(
        cls,
        ctx: commands.Context | disnake.ApplicationCommandInteraction = None,
        raise_exception: bool = True,
    ) -> bool:
        """Check if user has permission for command mod or above.

        When `ctx` is passed, it works as a function.
        When `ctx` is not passed, it acts as a decorator for a command.

        Returns
        -------
        bool
            True if user is an admin, False otherwise.
        Exception
            Throws `PermissionError` if `raise_exception=True` and user doesn't have permissions.
        """

        def predicate(ctx: commands.Context | disnake.ApplicationCommandInteraction) -> bool:
            if cls.is_bot_admin(ctx):
                return True
            if cls.role_check(ctx, PRIVILEGED_ROLES[:-2]):
                return True

            if raise_exception:
                raise PermissionError(message=Messages.mod_plus_only)
            return False

        if ctx:
            # If ctx is passed, return the result of the predicate
            return predicate(ctx)
        else:
            # If ctx is not passed, act as a decorator for command
            return commands.check(predicate)

    @classmethod
    def is_submod_plus(
        cls,
        ctx: commands.Context | disnake.ApplicationCommandInteraction = None,
        raise_exception: bool = True,
    ) -> bool:
        """Check if user has permission for command submod or above.

        When `ctx` is passed, it works as a function.
        When `ctx` is not passed, it acts as a decorator for a command.

        Returns
        -------
        bool
            True if user is an admin, False otherwise.
        Exception
            Throws `PermissionError` if `raise_exception=True` and user doesn't have permissions.
        """

        def predicate(ctx: commands.Context | disnake.ApplicationCommandInteraction) -> bool:
            if cls.is_bot_admin(ctx):
                return True
            if cls.role_check(ctx, PRIVILEGED_ROLES[:-1]):
                return True

            if raise_exception:
                raise PermissionError(message=Messages.submod_plus_only)
            return False

        if ctx:
            # If ctx is passed, return the result of the predicate
            return predicate(ctx)
        else:
            # If ctx is not passed, act as a decorator for command
            return commands.check(predicate)

    @classmethod
    def is_helper_plus(
        cls,
        ctx: commands.Context | disnake.ApplicationCommandInteraction = None,
        raise_exception: bool = True,
    ) -> bool:
        """Check if user has permission for command helper or above.

        When `ctx` is passed, it works as a function.
        When `ctx` is not passed, it acts as a decorator for a command.

        Returns
        -------
        bool
            True if user is an admin, False otherwise.
        Exception
            Throws `PermissionError` if `raise_exception=True` and user doesn't have permissions.
        """

        def predicate(ctx: commands.Context | disnake.ApplicationCommandInteraction) -> bool:
            if cls.is_bot_admin(ctx):
                return True
            if cls.role_check(ctx, PRIVILEGED_ROLES):
                return True

            if raise_exception:
                raise PermissionError(message=Messages.helper_plus_only)
            return False

        if ctx:
            # If ctx is passed, return the result of the predicate
            return predicate(ctx)
        else:
            # If ctx is not passed, act as a decorator for command
            return commands.check(predicate)

    @classmethod
    def role_check(
        cls, ctx: commands.Context | disnake.ApplicationCommandInteraction, roles: list[int]
    ) -> bool:
        """Check if user has role that enables him to use specific command.

        Returns
        -------
        bool
            True if user has required role, False otherwise.
        """

        guild = ctx.bot.get_guild(config.guild_id)
        user = guild.get_member(ctx.author.id)
        for role in user.roles:
            if role.id in roles:
                return True
        return False

    @classmethod
    def is_in_modroom(
        cls,
        ctx: commands.Context | disnake.ApplicationCommandInteraction = None,
        raise_exception: bool = True,
    ) -> bool:
        """Check if the command is invoked in modroom"""

        def predicate(ctx: commands.Context | disnake.ApplicationCommandInteraction) -> bool:
            if ctx.channel.id == config.mod_room:
                return True

            if raise_exception:
                raise InvalidRoomError(Messages.specific_room_only(room=config.mod_room))
            return False

        if ctx:
            # If ctx is passed, return the result of the predicate
            return predicate(ctx)
        else:
            # If ctx is not passed, act as a decorator for command
            return commands.check(predicate)

    @classmethod
    def is_in_voteroom(
        cls,
        ctx: commands.Context | disnake.ApplicationCommandInteraction = None,
        raise_exception: bool = True,
    ) -> bool:
        """Check if the command is invoked in voteroom"""

        def predicate(ctx: commands.Context | disnake.ApplicationCommandInteraction) -> bool:
            if ctx.channel.id == config.vote_room:
                return True

            if raise_exception:
                raise InvalidRoomError(Messages.specific_room_only(room=config.vote_room))
            return False

        if ctx:
            # If ctx is passed, return the result of the predicate
            return predicate(ctx)
        else:
            # If ctx is not passed, act as a decorator for command
            return commands.check(predicate)

    @classmethod
    def is_botroom(cls, inter: disnake.ApplicationCommandInteraction) -> bool:
        """
        Check if the interaction is in allowed channel. This is used to change response type to ephemeral.

        Returns
        -------
        bool
            False if user is not in DMs | thread | allowed channel. Otherwise True.
        """

        # DMs with bot
        if inter.guild is None:
            return False

        # allow threads in channels
        if isinstance(inter.channel, disnake.Thread):
            return False

        # allowed channels
        if inter.channel_id in config.allowed_channels:
            return False

        return True
