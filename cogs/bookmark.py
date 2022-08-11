import disnake
from disnake.ext import commands
from features.bookmark import BookmarkFeatures
from modals.bookmark import BookmarkModal
from buttons.bookmark import BookmarkView
import utils


class Bookmark(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.message_command(name="Bookmark")
    async def bookmark(self, inter: disnake.ApplicationCommandInteraction, message: disnake.Message):
        """Send modal with input for bookmark name and then send to user"""
        await inter.response.send_modal(modal=BookmarkModal(message))

    async def bookmark_reaction(self, ctx):
        embed, images, files_attached = await BookmarkFeatures.create_bookmark_embed(self, ctx)
        try:
            if images:
                for image in images:
                    embed.append(await BookmarkFeatures.create_image_embed(self, ctx, image))
            await ctx.member.send(embeds=embed, view=BookmarkView(), files=files_attached)
        except disnake.HTTPException as e:
            if e.code == 50007:
                await ctx.channel.send(utils.fill_message("blocked_bot", author=ctx.member.mention))
            else:
                raise e

    @commands.Cog.listener()
    async def on_button_click(self, inter: disnake.MessageInteraction):
        if inter.component.custom_id != "bookmark:delete":
            return
        await inter.message.delete()


def setup(bot):
    bot.add_cog(Bookmark(bot))
