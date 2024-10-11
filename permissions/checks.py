"""All checks for role and user permissions"""

import disnake
from disnake.ext import commands

from config.app_config import config
from utils.errors import (
    NotBotAdminError,
    NotHelperPlusError,
    NotModPlusError,
    NotSubmodPlusError,
)

priviliged_roles = [config.bot_admin_role, config.mod_role, config.submod_role, config.helper_role]


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
            Throws `NotAdminError` if `raise_exception=True` and user doesn't have permissions.
        """

        def predicate(ctx: commands.Context | disnake.ApplicationCommandInteraction) -> bool:
            if config.bot_admin_role in ctx.author.roles:
                return True
            if raise_exception:
                raise NotBotAdminError
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
            Throws `NotModPlusError` if `raise_exception=True` and user doesn't have permissions.
        """

        def predicate(ctx: commands.Context | disnake.ApplicationCommandInteraction) -> bool:
            if cls.role_check(ctx, priviliged_roles[:-2]):
                return True

            if raise_exception:
                raise NotModPlusError
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
            Throws `NotSubmodPlusError` if `raise_exception=True` and user doesn't have permissions.
        """

        def predicate(ctx: commands.Context | disnake.ApplicationCommandInteraction) -> bool:
            if cls.role_check(ctx, priviliged_roles[:-1]):
                return True

            if raise_exception:
                raise NotSubmodPlusError
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
            Throws `NotHelperPlusError` if `raise_exception=True` and user doesn't have permissions.
        """

        def predicate(ctx: commands.Context | disnake.ApplicationCommandInteraction) -> bool:
            if cls.role_check(ctx, priviliged_roles):
                return True

            if raise_exception:
                raise NotHelperPlusError
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
