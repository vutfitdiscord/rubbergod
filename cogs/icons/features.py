import disnake

import utils
from cogs.base import Base
from rubbergod import Rubbergod


def remove_prefix(text, prefix) -> str:
    if text.startswith(prefix):
        return text[len(prefix) :]
    return text


def icon_name(icon: disnake.Role) -> str:
    return remove_prefix(icon.name, Base.config.icon_role_prefix)


def icon_emoji(bot: Rubbergod, icon_role: disnake.Role) -> disnake.PartialEmoji | None:
    emoji = icon_role.emoji
    if emoji is not None:  # Return Role Emoji if it is a server emoji
        return emoji
    icon = icon_name(icon_role)
    guild = bot.get_guild(Base.config.guild_id)
    emoji = utils.get_emoji(guild=guild, name=icon)
    if emoji is not None:
        return emoji
    try:
        rules = Base.config.icon_rules[icon_role.id]
        emoji_id = rules.get("emoji_id")
        emoji = bot.get_emoji(emoji_id)
        return emoji
    except (AttributeError, KeyError):
        return None


def get_icon_roles(guild: disnake.Guild) -> list[disnake.Role]:
    return [role for role in guild.roles if role.id in Base.config.icon_roles]


async def can_assign(icon: disnake.Role, user: disnake.Member) -> bool:
    """Whether a given user can have a given icon"""
    rules = Base.config.icon_rules[icon.id]
    user_roles = {role.id for role in user.roles}
    allow = rules.get("allow")
    deny = rules.get("deny", [])
    allowed_by_role = allow is None or not user_roles.isdisjoint(allow)
    allowed_by_user = allow is None or user.id in allow
    denied = deny is not None and (not user_roles.isdisjoint(deny) or user.id in deny)
    return (allowed_by_role or allowed_by_user) and not denied


async def do_set_icon(icon: disnake.Role, user: disnake.Member) -> None:
    """Set the icon to the user, removing any previous icons,
    without checking whether the user is allowed to have said icon
    """
    icon_roles = get_icon_roles(user.guild)
    current_roles = [role for role in user.roles if role in icon_roles]
    if current_roles == [icon]:
        return
    if current_roles:
        await user.remove_roles(*current_roles)
    if icon:
        await user.add_roles(icon)


async def icon_autocomp(inter: disnake.ApplicationCommandInteraction, partial: str) -> list[str]:
    icon_roles = get_icon_roles(inter.guild)
    names = (icon_name(role) for role in icon_roles)
    return [name for name in names if partial.casefold() in name.casefold()]


def get_icon_emoji(icon: disnake.Role) -> str | disnake.Emoji | disnake.PartialEmoji:
    emoji = getattr(icon, "_icon", None)
    if type(emoji) not in [str, disnake.Emoji, disnake.PartialEmoji]:
        emoji = None
    return emoji
