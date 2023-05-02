"""
Cog for meme commands.
"""

from io import BytesIO
from random import choice
from typing import List

import disnake
import requests
from disnake.ext import commands
from PIL import Image

import utils
from cogs.base import Base
from config import cooldowns
from config.app_config import config
from config.messages import Messages

uhoh_counter = 0


class Meme(Base, commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: disnake.message):
        global uhoh_counter

        if message.author.bot:
            if (
                message.author.id in config.grillbot_ids
                and message.content.startswith("<:")
                and message.content.endswith(">")
            ):
                await message.channel.send(message.content)
            return

        elif config.uhoh_string in message.content.lower():
            await message.channel.send("uh oh")
            uhoh_counter += 1
        elif message.content == "PR":
            await message.channel.send(Messages.pr_meme)

    @commands.slash_command(name="uhoh", description=Messages.uhoh_brief)
    async def uhoh(self, inter):
        await inter.send(utils.fill_message("uhoh_counter", uhohs=uhoh_counter))

    # Ignore '??'
    @commands.command(name="?")
    async def ignore_questionmark(self, ctx):
        pass

    @cooldowns.short_cooldown
    @commands.command(name="??", brief="???")
    async def question(self, ctx):
        await ctx.send(choice(Messages.question))

    @cooldowns.short_cooldown
    @commands.slash_command(name="bonk", description=Messages.bonk_brief)
    async def bonk(self, inter, user: disnake.User = None):
        """Bonk someone
        user: disnake.User. If none, the bot will bonk you.
        """
        await inter.response.defer()
        if user is None:
            bonked = inter.author
        else:
            bonked = user

        if not bonked.avatar:
            url = bonked.display_avatar.with_format("png")
        else:
            url = bonked.display_avatar.with_format("jpg")
        response = requests.get(url)
        avatar = Image.open(BytesIO(response.content))

        if not bonked.avatar:
            avatar = avatar.convert('RGB')

        frames = self.get_bonk_frames(avatar)

        with BytesIO() as image_binary:
            frames[0].save(
                image_binary,
                format="GIF",
                save_all=True,
                append_images=frames[1:],
                duration=30,
                loop=0,
                transparency=0,
                disposal=2,
                optimize=False,
            )
            image_binary.seek(0)
            await inter.send(file=disnake.File(fp=image_binary, filename="bonk.gif"))

    def get_bonk_frames(self, avatar: Image.Image) -> List[Image.Image]:
        """Get frames for the bonk"""
        frames = []
        width, height = 200, 170
        deformation = (0, 0, 0, 5, 10, 20, 15, 5)

        avatar = utils.round_image(avatar.resize((100, 100)))

        for i in range(8):
            img = "%02d" % (i + 1)
            frame = Image.new("RGBA", (width, height), (54, 57, 63, 1))
            bat = Image.open(f"images/bonk/{img}.png")

            frame_avatar = avatar.resize((100, 100 - deformation[i]))

            frame.paste(frame_avatar, (80, 60 + deformation[i]), frame_avatar)
            frame.paste(bat, (10, 5), bat)
            frames.append(frame)

        return frames


def setup(bot):
    bot.add_cog(Meme(bot))
