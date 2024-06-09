"""
Cog for creating gifs.
"""

from io import BytesIO

import disnake
from disnake.ext import commands
from PIL import Image

from cogs.base import Base
from config import cooldowns
from rubbergod import Rubbergod

from .features import IMAGES_PATH, ImageHandler
from .messages_cz import MessagesCZ

MISSING = disnake.utils.MISSING


class Gif(Base, commands.Cog):
    def __init__(self, bot: Rubbergod):
        super().__init__()
        self.bot = bot
        self.imagehandler = ImageHandler()

    async def get_profile_picture(self, user: disnake.User, size: int = MISSING, format: str = "png"):
        avatar = await user.display_avatar.replace(size=size, format=format).read()
        avatarFull = Image.open(BytesIO(avatar)).convert("RGBA")
        return avatarFull

    @cooldowns.default_cooldown
    @commands.slash_command(name="pet", description=MessagesCZ.pet_brief)
    async def pet(self, inter: disnake.ApplicationCommandInteraction, user: disnake.User = None):
        await inter.response.defer()
        user = inter.author if user is None else user
        avatar = await self.get_profile_picture(user)
        avatar = ImageHandler.square_to_circle(avatar)

        frames = []
        deformWidth = [-1, -2, 1, 2, 1]
        deformHeight = [4, 3, 1, 1, -4]
        width, height = 80, 80
        x, y = 112, 122

        images_path = IMAGES_PATH / "pet"

        for i in range(5):
            frame = Image.new("RGBA", (x, y), (0, 0, 0, 0))
            hand = Image.open(f"{images_path}/{i}.png")
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
            await inter.send(file=disnake.File(fp=image_binary, filename="pet.gif"))

    @cooldowns.default_cooldown
    @commands.slash_command(name="catnap", description="Catnap your friend")
    async def catnap(self, inter: disnake.ApplicationCommandInteraction, user: disnake.User = None):
        await inter.response.defer()
        user = inter.author if user is None else user
        avatar = await self.get_profile_picture(user, 64)

        width, height = avatar.size
        if width != 64 or height != 64:
            avatar = avatar.resize((64, 64))

        # clear alpha channel
        avatar = avatar.convert("P", palette=Image.ADAPTIVE, colors=200).convert("RGBA")
        avatar = self.imagehandler.square_to_circle(avatar)
        avatar = avatar.convert("P", palette=Image.ADAPTIVE, colors=200).convert("RGBA")
        with BytesIO() as image_binary:
            ImageHandler.render_catnap(image_binary, avatar)
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
        avatar = await self.get_profile_picture(user, 64)

        frames = ImageHandler.get_bonk_frames(avatar)

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
