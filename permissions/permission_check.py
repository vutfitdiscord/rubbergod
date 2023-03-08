"""All checks for role and user permissions"""

from config.app_config import config
from typing import Union
import disnake
from disnake.ext import commands


allowed_roles = [config.mod_role, config.submod_role, config.helper_role]


def is_bot_admin(ctx: Union[commands.Context, disnake.ApplicationCommandInteraction]):
    """Check if user is bot admin"""
    return ctx.author.id in config.admin_ids


def role_check(ctx, roles):
    guild = ctx.bot.get_guild(config.guild_id)
    user = guild.get_member(ctx.author.id)
    for role in user.roles:
        if role.id in roles:
            return True
    return is_bot_admin(ctx)


def helper_plus(ctx):
    """Check if user has permission for command helper or above."""
    return role_check(ctx, allowed_roles)


def submod_plus(ctx):
    """Check if user has permission for command submod or above."""
    return role_check(ctx, allowed_roles[:-1])


def mod_plus(ctx):
    """Check if user has permission for command mod or above."""
    return role_check(ctx, allowed_roles[:-2])
