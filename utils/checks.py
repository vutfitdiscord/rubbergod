"""
Contains functions to check permissions of users, channels and other.
"""

from typing import Callable

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
    """Class containing methods to check permissions

    Methods using `check_template` are used as decorators for commands or as normal functions.
    """

    @classmethod
    def is_bot_admin(
        cls,
        ctx: commands.Context | disnake.ApplicationCommandInteraction = None,
        raise_exception: bool = True,
    ):
        """Check if the user is a bot admin."""
        return cls.check_template(
            ctx,
            lambda ctx: ctx.author.id in config.admin_ids,
            raise_exception,
            PermissionError(Messages.bot_admin_only),
        )

    @classmethod
    def is_mod_plus(
        cls,
        ctx: commands.Context | disnake.ApplicationCommandInteraction = None,
        raise_exception: bool = True,
    ):
        """Check if user has permission for command mod or above."""
        return cls.check_template(
            ctx,
            lambda ctx: (
                cls.is_bot_admin(ctx, raise_exception=False) or cls.role_check(ctx, PRIVILEGED_ROLES[:-2])
            ),
            raise_exception,
            PermissionError(Messages.mod_plus_only),
        )

    @classmethod
    def is_submod_plus(
        cls,
        ctx: commands.Context | disnake.ApplicationCommandInteraction = None,
        raise_exception: bool = True,
    ):
        """Check if user has permission for command submod or above."""

        return cls.check_template(
            ctx,
            lambda ctx: (
                cls.is_bot_admin(ctx, raise_exception=False) or cls.role_check(ctx, PRIVILEGED_ROLES[:-1])
            ),
            raise_exception,
            PermissionError(Messages.submod_plus_only),
        )

    @classmethod
    def is_helper_plus(
        cls,
        ctx: commands.Context | disnake.ApplicationCommandInteraction = None,
        raise_exception: bool = True,
    ):
        """Check if user has permission for command helper or above."""
        return cls.check_template(
            ctx,
            lambda ctx: (
                cls.is_bot_admin(ctx, raise_exception=False) or cls.role_check(ctx, PRIVILEGED_ROLES)
            ),
            raise_exception,
            PermissionError(Messages.helper_plus_only),
        )

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
    ):
        """Check if the command is invoked in modroom"""
        return cls.check_template(
            ctx,
            lambda ctx: ctx.channel.id == config.mod_room,
            raise_exception,
            InvalidRoomError(Messages.specific_room_only(room=config.mod_room)),
        )

    @classmethod
    def is_in_voteroom(
        cls,
        ctx: commands.Context | disnake.ApplicationCommandInteraction = None,
        raise_exception: bool = True,
    ):
        """Check if the command is invoked in voteroom"""
        return cls.check_template(
            ctx,
            lambda ctx: ctx.channel.id == config.vote_room,
            raise_exception,
            InvalidRoomError(Messages.specific_room_only(room=config.vote_room)),
        )

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

    @classmethod
    def check_template(
        cls,
        ctx: commands.Context | disnake.ApplicationCommandInteraction,
        check: Callable,
        raise_exception: bool,
        exception: Exception,
    ) -> bool:
        """Check if the command is invoked in voteroom

        When `ctx` is passed, it works as a function.
        When `ctx` is not passed, it acts as a decorator for a command.

        Returns
        -------
        bool
            based on the passed check
        Exception
            Throws `Exception` if `raise_exception=True` and `check=False`
        """

        def predicate(ctx: commands.Context | disnake.ApplicationCommandInteraction) -> bool:
            if check(ctx):
                return True
            if raise_exception:
                raise exception
            return False

        if ctx:
            # If ctx is passed, return the result of the predicate
            return predicate(ctx)
        else:
            # If ctx is not passed, act as a decorator for command
            return commands.check(predicate)
