import discord
from discord.ext import commands

import utils
from config import app_config as config, messages

from PIL import Image, ImageOps, ImageDraw
import sys

from io import BytesIO
import requests

config = config.Config
messages = messages.Messages


class Pet(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)
    @commands.command(aliases=[])
    async def pet(self, ctx, user: discord.Member = None):
        if user is None:
            user = ctx.author      
        url = user.avatar_url_as(format='jpg')
        response = requests.get(url)
        avatarFull = Image.open(BytesIO(response.content))

        frames = []
        deformWidth = [-1, -2, 1, 2, 1]
        deformHeight = [4, 3, 1, 1, -4]
        width = 80
        height = 80

        for i in range(5):
            frame = Image.new('RGBA', (112,112), (255,255,255, 1))
            hand = Image.open('images/pet/' + str(i) + '.png')

            avatar = avatarFull
            width = width - deformWidth[i]
            height = height - deformHeight[i]
            avatar = avatar.resize((width,height))       
            size = (avatar.size)
            mask = Image.new('1', size, 0)
            draw = ImageDraw.Draw(mask) 
            draw.ellipse((0, 0) + size, fill=255)
            avatar.putalpha(mask)

            frame.paste(avatar, (112 - width, 112 - height), avatar)
            frame.paste(hand,(0,0), hand)
            frames.append(frame)  

        with BytesIO() as image_binary:           
            frames[0].save(image_binary, format='GIF', save_all=True, append_images=frames[1:], duration=40, loop=0, transparency=0, disposal=2, optimize=False)
            image_binary.seek(0)
            await ctx.send(file=discord.File(fp=image_binary, filename="pet.gif"))

    @pet.error
    async def pet_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(utils.fill_message("member_not_found", user=ctx.author.id))

def setup(bot):
    bot.add_cog(Pet(bot))
