import disnake
from disnake.ext import commands
from config.messages import Messages
import utils


class Override(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.check(utils.is_bot_admin)
    @commands.slash_command(name="override", description=Messages.override_brief)
    async def override(
        self,
        inter: disnake.ApplicationCommandInteraction,
        channel_name,
        role: disnake.Role,
        category: disnake.CategoryChannel = None
    ):

        await inter.response.defer()
        guild = inter.guild
        overwrites = {guild.default_role: disnake.PermissionOverwrite(view_channel=False)}
        for member in role.members:
            overwrites[guild.get_member(member.id)] = disnake.PermissionOverwrite(view_channel=True)

        channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)
        await inter.edit_original_message(
            utils.fill_message(
                "override_success",
                channel=channel.mention,
                role=role.name
            )
        )


def setup(bot):
    bot.add_cog(Override(bot))
