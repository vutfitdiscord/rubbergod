"""All checks for role and user permissions"""

from typing import Union

import disnake
from disnake.ext import commands

from config.app_config import config
from config.messages import Messages

allowed_roles = [config.mod_role, config.submod_role, config.helper_role]


class NotAdminError(commands.CommandError):
    """An error indicating that a user doesn't have permissions to use
    a command that is available only to admins of bot.
    """
    def __init__(self) -> None:
        self.message = Messages.bot_admin_only


def is_bot_admin(
    ctx: Union[commands.Context, disnake.ApplicationCommandInteraction],
    raise_exception: bool = True
):
    """
    Check if user is bot admin.
    if raise_exception=False return False instead of raising error
    """
    if ctx.author.id in config.admin_ids:
        return True

    if not raise_exception:
        return False
    raise NotAdminError


def role_check(ctx, roles, MissingPermission, raise_exception=True):
    """
    Check if user has permission for command.
    if raise_exception=False return False instead of raising error
    """
    guild = ctx.bot.get_guild(config.guild_id)
    user = guild.get_member(ctx.author.id)
    for role in user.roles:
        if role.id in roles:
            return True
    if ctx.author.id in config.admin_ids:
        return True
    if not raise_exception:
        return False
    raise MissingPermission


class NotHelperPlusError(commands.CommandError):
    """An error indicating that a user doesn't have permissions to use
    a command that is available only to helpers and above.
    """
    def __init__(self) -> None:
        self.message = Messages.helper_plus_only


def helper_plus(ctx, raise_exception=True):
    """Check if user has permission for command helper or above."""
    return role_check(ctx, allowed_roles, NotHelperPlusError, raise_exception)


class NotSubmodPlusError(commands.CommandError):
    """An error indicating that a user doesn't have permissions to use
    a command that is available only to submods and above.
    """
    def __init__(self) -> None:
        self.message = Messages.submod_plus_only


def submod_plus(ctx, raise_exception=True):
    """Check if user has permission for command submod or above."""
    return role_check(ctx, allowed_roles[:-1], NotSubmodPlusError, raise_exception)


class NotModPlusError(commands.CommandError):
    """An error indicating that a user doesn't have permissions to use
    a command that is available only to mods and above.
    """
    def __init__(self) -> None:
        self.message = Messages.mod_plus_only


def mod_plus(ctx, raise_exception=True):
    """Check if user has permission for command mod or above."""
    return role_check(ctx, allowed_roles[:-2], NotModPlusError, raise_exception)
