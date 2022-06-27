import disnake
from disnake.ext import commands
from modals.bookmark import BookmarkModal


class Bookmark(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.message_command(name="Bookmark")
    async def bookmark(self, inter: disnake.ApplicationCommandInteraction, message: disnake.Message):
        """Send modal with input for bookmark name and then send to user"""
        await inter.response.send_modal(modal=BookmarkModal(message))

    @commands.Cog.listener()
    async def on_button_click(self, inter: disnake.MessageInteraction):
        if inter.component.custom_id != "bookmark:delete":
            return
        await inter.message.delete()


def setup(bot):
    bot.add_cog(Bookmark(bot))
