"""
Functions for server moderation and help functions for mods
"""

import disnake
from disnake.ext import commands

from config.app_config import config
from buttons.moderation import ModerationView
from datetime import datetime
import utils


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.moderation_true = "moderation:resolve:true"
        self.moderation_false = "moderation:resolve:false"

    async def mod_tag(self, message: disnake.Message, title, room):
        if len(message.content) < 3800:
            embed = disnake.Embed(
                title=f"Tag {title} used in #{message.channel.name}",
                description=f"**User:** {message.author.mention}\n"
                f"**Room:** {message.channel.mention}\n"
                f"**Content:**\n{message.content}",
                color=disnake.Colour.yellow()
            )
        else:
            embed = disnake.Embed(
                title=f"Tag {title} used in #{message.channel.name}",
                description=f"**User:** {message.author.mention}\n"
                f"**Room:** {message.channel.mention}\n",
                color=disnake.Colour.yellow()
            )
            parts = utils.split_to_parts(message.content, 1024)
            for msg in parts:
                embed.add_field(name="Content", value=msg, inline=False)

        embed.add_field(name="Resolved by:", value="---")
        embed.set_footer(text=datetime.now().strftime('%d.%m.%Y %H:%M'))
        await room.send(
            embed=embed,
            view=ModerationView(
                message.jump_url,
                "Unresolved",
                disnake.ButtonStyle.gray,
                self.moderation_false
            )
        )

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        """Logs use of @mod, @submod and @helper tag and send message to designated room"""

        if f"<@&{config.mod_role}>" in message.content:
            await self.mod_tag(message, "@mod", self.bot.get_channel(config.mod_room))

        elif f"<@&{config.submod_role}>" in message.content or f"<@&{config.helper_role}>" in message.content:
            await self.mod_tag(message, "@submod/@helper", self.bot.get_channel(config.submod_helper_room))

    @commands.Cog.listener()
    async def on_button_click(self, inter: disnake.MessageInteraction):
        if inter.component.custom_id not in [self.moderation_true, self.moderation_false]:
            return

        embed = inter.message.embeds[0].to_dict()
        if inter.component.custom_id == self.moderation_true:
            label = "Unresolved"
            style = disnake.ButtonStyle.gray
            custom_id = self.moderation_false
            for field in embed["fields"]:
                if field["name"] == "Resolved by:":
                    field["value"] = "---"

        else:
            label = "Resolved"
            style = disnake.ButtonStyle.green
            custom_id = self.moderation_true
            for field in embed["fields"]:
                if field["name"] == "Resolved by:":
                    field["value"] = inter.author.mention

        await inter.response.edit_message(
            embed=disnake.Embed.from_dict(embed),
            view=ModerationView(inter.message.jump_url, label, style, custom_id)
        )


def setup(bot):
    bot.add_cog(Moderation(bot))
