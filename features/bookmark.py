import disnake
import re
from utils import split_to_parts
from config.messages import Messages


class BookmarkFeatures():
    def __init__(self, bot):
        self.bot = bot

    def check_profile_picture(self, inter, embed):
        if inter.message.author.avatar:
            return embed.set_author(name=inter.message.author, icon_url=inter.message.author.avatar)
        else:
            return embed.set_author(name=inter.message.author)

    async def create_image_embed(self, inter, image, title_name=Messages.bookmark_title):
        """Create embed from image only"""
        embed = disnake.Embed(title=title_name, color=inter.message.author.colour)
        if inter.message.author.avatar:
            embed.set_author(name=inter.message.author, icon_url=inter.message.author.avatar)
        else:
            embed.set_author(name=inter.message.author)
        embed.set_image(image)
        embed.add_field(
            name="Channel",
            value=f"[Jump to original message]({inter.message.jump_url}) in {inter.message.channel.mention}"
        )
        return embed

    async def create_bookmark_embed(self, inter, title_name=Messages.bookmark_title):
        embed = disnake.Embed(title=title_name, colour=inter.message.author.colour)
        if inter.message.author.avatar:
            embed.set_author(name=inter.message.author, icon_url=inter.message.author.avatar)
        else:
            embed.set_author(name=inter.message.author)

        content = ""
        if inter.message.embeds:
            for embed in inter.message.embeds:
                embed.title, embed.colour = title_name, inter.message.author.colour
                if inter.message.author.avatar:
                    embed.set_author(name=inter.message.author, icon_url=inter.message.author.avatar)
                else:
                    embed.set_author(name=inter.message.author)

        if inter.message.content:
            content = inter.message.content
        else:
            content += "*Empty*"

        # create list of attachments
        images = []
        files_attached = []
        if inter.message.attachments:
            for attachment in inter.message.attachments:
                if re.search(r"\.png|\.jpg|\.jpeg|\.gif$", str(attachment)):
                    images.append(attachment)
                else:
                    files_attached.append(await attachment.to_file())

        if images:
            embed.set_image(images[0])
            del images[0]
        if len(content) > 1024:
            parts = split_to_parts(content, 1024)
            for msg in parts:
                embed.add_field(name="Původní zpráva", value=msg, inline=False)
        else:
            embed.add_field(name="Původní zpráva", value=content, inline=False)
        embed.add_field(
            name="Channel",
            value=f"[Jump to original message]({inter.message.jump_url}) in {inter.message.channel.mention}"
        )
        return ([embed], images, files_attached)
