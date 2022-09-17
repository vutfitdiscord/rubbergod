from dis import dis
from enum import auto
from disnake.ext import commands
from config.app_config import Config
import utils
import disnake
from config.app_config import config
from config.messages import Messages


def icon_name(icon: disnake.Role):
    return icon.name.removeprefix(config.icon_role_prefix)


def get_icon_roles(guild: disnake.Guild):
    return [role for role in guild.roles if role.id in config.icon_roles]


async def icon_autocomp(inter: disnake.ApplicationCommandInteraction, partial: str):
    icon_roles = get_icon_roles(inter.guild)
    names = (icon_name(role) for role in icon_roles)
    return [name for name in names if partial.casefold() in name.casefold()]


class Icons(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def do_set_icon(self, icon: disnake.Role, user: disnake.Member):
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

    async def can_assign(self, icon: disnake.Role, user: disnake.Member):
        """Whether a given user can have a given icon"""
        rules = config.icon_rules[icon.id]
        user_roles = {role.id for role in user.roles}
        allow = rules.get("allow")
        deny = rules.get("deny", [])
        return (allow is None or not user_roles.isdisjoint(allow)) and user_roles.isdisjoint(deny)

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

        await inter.response.send_message(embed=embed)

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
