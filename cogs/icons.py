"""
Cog implementing dynamic icon system. Users can assign themselves icons from a list of roles.
"""

from typing import List, Optional, Union

import disnake
from disnake.ext import commands

import utils
from buttons.general import TrashView
from cogs.base import Base
from config.messages import Messages


def remove_prefix(text, prefix) -> str:
    if text.startswith(prefix):
        return text[len(prefix):]
    return text


def icon_name(icon: disnake.Role) -> str:
    return remove_prefix(icon.name, Base.config.icon_role_prefix)


def icon_emoji(bot: commands.Bot, icon_role: disnake.Role) -> Optional[disnake.PartialEmoji]:
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


def get_icon_roles(guild: disnake.Guild) -> List[disnake.Role]:
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


class IconSelect(disnake.ui.Select):
    def __init__(self, bot: commands.Bot, **kwargs) -> None:
        super().__init__(**kwargs)
        self.bot = bot

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer(ephemeral=True)
        [choice] = self.values
        icon = disnake.utils.get(inter.guild.roles, id=int(choice))
        if icon is None:
            await inter.edit_original_response(Messages.icon_ui_fail)
            return
        user = inter.user
        if await can_assign(icon, user):
            await inter.edit_original_response(Messages.icon_set_success(
                        user=inter.user,
                        icon=icon_emoji(self.bot, icon) or icon_name(icon)),
                        view=None)
            await do_set_icon(icon, user)
        else:
            await inter.edit_original_response(Messages.icon_ui_no_permission)


async def icon_autocomp(inter: disnake.ApplicationCommandInteraction, partial: str) -> str:
    icon_roles = get_icon_roles(inter.guild)
    names = (icon_name(role) for role in icon_roles)
    return [name for name in names if partial.casefold() in name.casefold()]


def get_icon_emoji(icon: disnake.Role) -> Union[str, disnake.Emoji, disnake.PartialEmoji]:
    emoji = getattr(icon, "_icon", None)
    if type(emoji) not in [str, disnake.Emoji, disnake.PartialEmoji]:
        emoji = None
    return emoji


class Icons(Base, commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    @utils.PersistentCooldown(command_name="icon", limit=Base.config.icon_ui_cooldown)
    @commands.slash_command(description=Messages.icon_ui, guild_ids=[Base.config.guild_id])
    async def icon(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)
        icon_roles = get_icon_roles(inter.guild)
        user = inter.user
        options = [
            disnake.SelectOption(
                label=icon_name(icon), value=str(icon.id), emoji=icon_emoji(self.bot, icon)
            )
            for icon in icon_roles
            if await can_assign(icon, user)
        ]
        view = TrashView("icon:delete", row=4)      # makes it last row so it's always under the dropdown
        for row, start_i in enumerate(range(0, len(options), 25)):
            # 25 is the max number of options per select
            component = IconSelect(
                bot=self.bot,
                placeholder=Messages.icon_ui_choose,
                options=options[start_i: start_i + 25],
                row=row,
            )
            view.add_item(component)
        await inter.edit_original_response(view=view)

    @commands.Cog.listener()
    async def on_button_click(self, inter: disnake.MessageInteraction):
        if inter.component.custom_id != "icon:delete":
            return
        await do_set_icon(None, inter.author)
        await inter.response.send_message(content=Messages.icon_removed, ephemeral=True)

    async def cog_slash_command_error(
        self, inter: disnake.ApplicationCommandInteraction, error: Exception
    ) -> None:
        if isinstance(error, utils.PCommandOnCooldown):
            await inter.response.send_message(str(error), ephemeral=True)
            return True


def setup(bot):
    bot.add_cog(Icons(bot))
