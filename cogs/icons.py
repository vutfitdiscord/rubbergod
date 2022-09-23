import disnake
from disnake.ext import commands

from buttons.icon import IconView
from config.app_config import config
from config.messages import Messages
import utils


def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text


def icon_name(icon: disnake.Role):
    return remove_prefix(icon.name, config.icon_role_prefix)


def get_icon_roles(guild: disnake.Guild):
    return [role for role in guild.roles if role.id in config.icon_roles]


async def can_assign(icon: disnake.Role, user: disnake.Member):
    """Whether a given user can have a given icon"""
    rules = config.icon_rules[icon.id]
    user_roles = {role.id for role in user.roles}
    allow = rules.get("allow")
    deny = rules.get("deny", [])
    allowed_by_role = (allow is None or not user_roles.isdisjoint(allow)) and user_roles.isdisjoint(deny)
    return allowed_by_role and user.id not in deny


async def do_set_icon(icon: disnake.Role, user: disnake.Member):
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
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer(ephemeral=True)
        [choice] = self.values
        icon = disnake.utils.get(inter.guild.roles, id=int(choice))
        if icon is None:
            await inter.edit_original_message(Messages.icon_ui_fail)
            return
        user = inter.user
        if await can_assign(icon, user):
            await inter.edit_original_message(
                Messages.icon_set_success.format(user=inter.user, icon=icon_name(icon)), view=None
            )
            await do_set_icon(icon, user)
        else:
            await inter.edit_original_message(Messages.icon_ui_no_permission)


async def icon_autocomp(inter: disnake.ApplicationCommandInteraction, partial: str):
    icon_roles = get_icon_roles(inter.guild)
    names = (icon_name(role) for role in icon_roles)
    return [name for name in names if partial.casefold() in name.casefold()]


def get_icon_emoji(icon: disnake.Role):
    emoji = getattr(icon, "_icon", None)
    if type(emoji) not in [str, disnake.Emoji, disnake.PartialEmoji]:
        emoji = None
    return emoji


class Icons(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @utils.PersistentCooldown(command_name="icon", limit=config.icon_ui_cooldown)
    @commands.slash_command(description=Messages.icon_ui, guild_ids=[config.guild_id])
    async def icon(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)
        icon_roles = get_icon_roles(inter.guild)
        user = inter.user
        options = [
            disnake.SelectOption(
                label=icon_name(icon), value=str(icon.id), emoji=get_icon_emoji(icon)
            )
            for icon in icon_roles
            if await can_assign(icon, user)
        ]
        view = IconView()
        for start_i in range(0, len(options), 25):
            component = IconSelect(
                placeholder=Messages.icon_ui_choose, options=options[start_i: start_i + 25], row=0,
            )
            view.add_item(component)
        await inter.edit_original_message(view=view)


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
