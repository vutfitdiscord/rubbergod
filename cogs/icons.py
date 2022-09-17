from disnake.ext import commands
from buttons.base import BaseView
import utils
import disnake
from config.app_config import config
from config.messages import Messages


def icon_name(icon: disnake.Role):
    return icon.name.removeprefix(config.icon_role_prefix)


def get_icon_roles(guild: disnake.Guild):
    return [role for role in guild.roles if role.id in config.icon_roles]


async def can_assign(icon: disnake.Role, user: disnake.Member):
    """Whether a given user can have a given icon"""
    rules = config.icon_rules[icon.id]
    user_roles = {role.id for role in user.roles}
    allow = rules.get("allow")
    deny = rules.get("deny", [])
    return (allow is None or not user_roles.isdisjoint(allow)) and user_roles.isdisjoint(deny)


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
            await do_set_icon(icon, user)
        else:
            await inter.edit_original_message(Messages.icon_ui_no_permission)


async def icon_autocomp(inter: disnake.ApplicationCommandInteraction, partial: str):
    icon_roles = get_icon_roles(inter.guild)
    names = (icon_name(role) for role in icon_roles)
    return [name for name in names if partial.casefold() in name.casefold()]


class Icons(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description=Messages.icon_description)
    async def icon(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @commands.check(utils.helper_plus)
    @icon.sub_command(description=Messages.icon_modset)
    async def modset(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.Member,
        icon_s: str = commands.Param(autocomplete=icon_autocomp),
    ):
        icon_roles = get_icon_roles(inter.guild)
        try:
            icon = next(role for role in icon_roles if icon_s == icon_name(icon))
        except StopIteration:
            embed = disnake.Embed(title=Messages.icon_set_no_role)
        else:
            await self.do_set_icon(icon, user)
            embed = disnake.Embed(
                title=Messages.icon_set_success.format(user=user, icon=icon_name(icon)),
            )

        await inter.response.send_message(embed=embed, ephemeral=True)

    @icon.sub_command(description=Messages.icon_ui)
    async def ui(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)
        icon_roles = get_icon_roles(inter.guild)
        user = inter.user
        options = [
            disnake.SelectOption(
                label=icon_name(icon), value=str(icon.id), emoji=getattr(icon, "_icon", None)
            )
            for icon in icon_roles
            if await can_assign(icon, user)
        ]
        assert len(options) <= 25  # TODO: remove this limit
        component = IconSelect(placeholder=Messages.icon_ui_choose, options=options)
        view = BaseView()
        view.add_item(component)
        await inter.edit_original_message("A", view=view)

    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.errors.CheckFailure):
            await ctx.send(utils.fill_message("insufficient_rights", user=ctx.author.id))
            return True
        if isinstance(error, commands.errors.CommandInvokeError):
            if isinstance(error.__cause__, commands.errors.ExtensionAlreadyLoaded):
                await ctx.send(utils.fill_message("cog_is_loaded", cog=error.__cause__.name))
                return True
            elif isinstance(error.__cause__, commands.errors.ExtensionNotLoaded):
                await ctx.send(utils.fill_message("cog_is_unloaded", cog=error.__cause__.name))
                return True


def setup(bot):
    bot.add_cog(Icons(bot))
