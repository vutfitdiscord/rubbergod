import disnake
from disnake.ext import commands
from buttons.bookmark import BookmarkView
from modals.bookmark import BookmarkModal
from config.messages import Messages


class Bookmark(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.message_command(name="Bookmark")
    async def bookmark(self, inter: disnake.ApplicationCommandInteraction, message: disnake.Message):
        """Send modal with input for bookmark name and then sends to user"""
        await inter.response.send_modal(modal=BookmarkModal(message))

    @commands.Cog.listener("on_raw_reaction_add")
    async def bookmark_reaction(self, payload: disnake.RawReactionActionEvent):
        # send embed to user where he left reading
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

        if str(payload.emoji) == "🔖":
            if message.embeds:
                for embed in payload.message.embeds:
                    content = embed.to_dict()
            else:
                content = message.content
            embed = disnake.Embed(title=Messages.bookmark_title, color=payload.member.colour)
            embed.set_author(name=message.author, icon_url=message.author.avatar)
            embed.add_field(name="Zpráva", value=content, inline=False)
            embed.add_field(
                name="Channel",
                value=f"[Jump to original message]({message.jump_url}) in {message.channel.mention}"
            )
            await payload.member.send(embed=embed, view=BookmarkView())

    @commands.Cog.listener("on_button_click")
    async def cool_button_listener(self, inter: disnake.MessageInteraction):
        if inter.component.custom_id != "delete_bookmark":
            return
        await inter.message.delete()


def setup(bot):
    bot.add_cog(Bookmark(bot))
