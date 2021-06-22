from config.messages import Messages
import discord
from discord.ext import commands

import utils

from PIL import Image, ImageDraw

from io import BytesIO
import requests

from config import cooldowns


class Pet(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @cooldowns.short_cooldown
    @commands.command()
    async def pet(self, ctx, user: discord.Member = None):
        if user is None:
            user = ctx.author
        if not user.avatar:
            await ctx.send(Messages.pet_unsupported_image)
            return
        url = user.avatar_url_as(format='jpg')
        response = requests.get(url)
        avatarFull = Image.open(BytesIO(response.content))

        frames = []
        deformWidth = [-1, -2, 1, 2, 1]
        deformHeight = [4, 3, 1, 1, -4]
        width = 80
        height = 80

        for i in range(5):
            frame = Image.new('RGBA', (112, 112), (255, 255, 255, 1))
            hand = Image.open(f"images/pet/{i}.png")
            width = width - deformWidth[i]
            height = height - deformHeight[i]
            avatar = avatarFull.resize((width, height))
            avatarMask = Image.new('1', avatar.size, 0)
            draw = ImageDraw.Draw(avatarMask)
            draw.ellipse((0, 0) + avatar.size, fill=255)
            avatar.putalpha(avatarMask)

            frame.paste(avatar, (112 - width, 112 - height), avatar)
            frame.paste(hand, (0, 0), hand)
            frames.append(frame)

        with BytesIO() as image_binary:
            frames[0].save(image_binary, format='GIF', save_all=True,
                           append_images=frames[1:], duration=40,
                           loop=0, transparency=0, disposal=2, optimize=False)
            image_binary.seek(0)
            await ctx.send(file=discord.File(fp=image_binary, filename="pet.gif"))

    @pet.error
    async def pet_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(utils.fill_message("member_not_found", user=ctx.author.id))


def setup(bot):
    bot.add_cog(Pet(bot))
