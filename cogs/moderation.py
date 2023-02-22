"""
Functions for moderation of server and help functions for mods
"""

import disnake
from disnake.ext import commands

from config.app_config import config
from buttons.moderation import ModerationView
from datetime import datetime


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        """Logs use of @mod tag and send message to mod_room"""

        if f"<@&{config.mod_role}>" in message.content:
            mod_room = self.bot.get_channel(config.mod_room)
            embed = disnake.Embed(
                title=f"Tag @mods used in #{message.channel.name}",
                description=f"**User:** {message.author.mention}\n"
                f"**Room:** {message.channel.mention}\n"
                f"**Content:**\n{message.content}",
                color=disnake.Colour.yellow()
            )
            embed.add_field(name="Resolved by:", value="---")
            embed.set_footer(text=datetime.now().strftime('%d.%m.%Y %H:%M'))
            await mod_room.send(embed=embed, view=ModerationView(message.jump_url, embed.to_dict()))


def setup(bot):
    bot.add_cog(Moderation(bot))
