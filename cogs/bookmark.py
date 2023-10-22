"""
Cog controlling bookmarks. React with bookmark emoji and the bot will send copy of message to user.
"""

import disnake
from disnake.ext import commands

from buttons.bookmark import BookmarkView
from cogs.base import Base
from features.bookmark import BookmarkFeatures
from modals.bookmark import BookmarkModal


class Bookmark(Base, commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @commands.message_command(name="Bookmark", guild_ids=[Base.config.guild_id])
    async def bookmark(self, inter: disnake.ApplicationCommandInteraction, message: disnake.Message):
        """Send modal with input for bookmark name and then send to user"""
        await inter.response.send_modal(modal=BookmarkModal(message))

    async def bookmark_reaction(self, ctx):
        embed, images, files_attached = await BookmarkFeatures.create_bookmark_embed(self, ctx)
        if images:
            for image in images:
                embed.append(await BookmarkFeatures.create_image_embed(self, ctx, image))
        # when sending sticker there can be overflow of files
        if len(files_attached) <= 10:
            await ctx.member.send(
                embeds=embed,
                view=BookmarkView(ctx.message.jump_url),
                files=files_attached
            )
        else:
            await ctx.member.send(
                embeds=embed,
                view=BookmarkView(ctx.message.jump_url),
                files=files_attached[:10]
            )
            await ctx.member.send(files=files_attached[10:])


def setup(bot):
    bot.add_cog(Bookmark(bot))
