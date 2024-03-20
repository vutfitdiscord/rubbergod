"""
Cog for creating gifs.
"""

from io import BytesIO

import disnake
import requests
from disnake.ext import commands
from PIL import Image

from cogs.base import Base
from config import cooldowns
from features.imagehandler import ImageHandler

from .messages_cz import MessagesCZ


class Gif(Base, commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.imagehandler = ImageHandler()

    async def get_profile_picture(self, inter, url):
        try:
            response = requests.get(url, timeout=10)
        except requests.exceptions.RequestException:
            await inter.send(MessagesCZ.gif_req_error, ephemeral=True)
            return None
        avatar = Image.open(BytesIO(response.content)).convert("RGBA")
        return avatar

    @cooldowns.default_cooldown
    @commands.slash_command(name="pet", description=MessagesCZ.pet_brief)
    async def pet(self, inter: disnake.ApplicationCommandInteraction, user: disnake.User = None):
        user = inter.author if user is None else user
        url = user.display_avatar.with_format("png")
        avatar = await self.get_profile_picture(inter, url)
        if avatar is None:
            return
        avatar = self.imagehandler.square_to_circle(avatar)

        frames = []
        deformWidth = [-1, -2, 1, 2, 1]
        deformHeight = [4, 3, 1, 1, -4]
        width, height = 80, 80
        x, y = 112, 122

        for i in range(5):
            frame = Image.new("RGBA", (x, y), (0, 0, 0, 0))
            hand = Image.open(f"images/pet/{i}.png")
            width = width - deformWidth[i]
            height = height - deformHeight[i]
            avatar = avatar.resize((width, height))
            avatar = avatar.convert("P", palette=Image.ADAPTIVE, colors=200).convert("RGBA")

            frame.paste(avatar, (x - width, y - height), avatar)
            frame.paste(hand, (0, 0), hand)
            frames.append(frame)

        with BytesIO() as image_binary:
            frames[0].save(
                image_binary,
                format="GIF",
                save_all=True,
                append_images=frames[1:],
                duration=40,
                loop=0,
                transparency=0,
                disposal=2,
                optimize=False,
            )
            image_binary.seek(0)
            await inter.response.send_message(file=disnake.File(fp=image_binary, filename="pet.gif"))

    @cooldowns.default_cooldown
    @commands.slash_command(name="catnap", description="Catnap your friend")
    async def catnap(self, inter: disnake.ApplicationCommandInteraction, user: disnake.User):
        await inter.response.defer()
        url = user.display_avatar.replace(size=64, format="png")
        try:
            response = requests.get(url, timeout=10)
        except requests.exceptions.RequestException:
            await inter.send(MessagesCZ.gif_req_error, ephemeral=True)
            return
        avatar = Image.open(BytesIO(response.content)).convert("RGBA")

        width, height = avatar.size
        if width != 64 or height != 64:
            avatar = avatar.resize((64, 64))

        # clear alpha channel
        avatar = avatar.convert("P", palette=Image.ADAPTIVE, colors=200).convert("RGBA")
        avatar = self.imagehandler.square_to_circle(avatar)
        avatar = avatar.convert("P", palette=Image.ADAPTIVE, colors=200).convert("RGBA")
        with BytesIO() as image_binary:
            self.imagehandler.render_catnap(image_binary, avatar)
            await inter.send(file=disnake.File(fp=image_binary, filename="steal.gif"))
            return

    @cooldowns.default_cooldown
    @commands.slash_command(name="bonk", description=MessagesCZ.bonk_brief)
    async def bonk(self, inter: disnake.ApplicationCommandInteraction, user: disnake.User = None):
        """Bonk someone
        user: disnake.User. If none, the bot will bonk you.
        """
        await inter.response.defer()
        user = inter.author if user is None else user
        url = user.display_avatar.with_format("png")
        avatar = await self.get_profile_picture(inter, url)
        if avatar is None:
            return

        frames = self.imagehandler.get_bonk_frames(avatar)

        with BytesIO() as image_binary:
            frames[0].save(
                image_binary,
                format="GIF",
                save_all=True,
                append_images=frames[1:],
                duration=30,
                loop=0,
                disposal=2,
                optimize=False,
            )
            image_binary.seek(0)
            await inter.send(file=disnake.File(fp=image_binary, filename="bonk.gif"))
