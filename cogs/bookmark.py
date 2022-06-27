import disnake
from disnake.ext import commands
from modals.bookmark import BookmarkModal
from config.messages import Messages
from buttons.bookmark import BookmarkView


class Bookmark(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.message_command(name="Bookmark")
    async def bookmark(self, inter: disnake.ApplicationCommandInteraction, message: disnake.Message):
        """Send modal with input for bookmark name and then send to user"""
        await inter.response.send_modal(modal=BookmarkModal(message))

    async def bookmark_reaction(self, ctx):
        if ctx.message.embeds:
            for embed in ctx.message.embeds:
                content = embed.to_dict()
        else:
            content = ctx.message.content
        embed = disnake.Embed(title=Messages.bookmark_title, color=ctx.member.colour)
        embed.set_author(name=ctx.message.author, icon_url=ctx.message.author.avatar)
        embed.add_field(name="Zpráva", value=content, inline=False)
        embed.add_field(
            name="Channel",
            value=f"[Jump to original message]({ctx.message.jump_url}) in {ctx.message.channel.mention}"
        )
        try:
            await ctx.member.send(embed=embed, view=BookmarkView())
            return
        except disnake.HTTPException:
            return

    @commands.Cog.listener()
    async def on_button_click(self, inter: disnake.MessageInteraction):
        if inter.component.custom_id != "bookmark:delete":
            return
        await inter.message.delete()


def setup(bot):
    bot.add_cog(Bookmark(bot))
