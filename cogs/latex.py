import aiohttp
import discord
from discord.ext import commands
import io
import urllib
from PIL import Image

from config import messages

messages = messages.Messages

PNG_HEADER = b'\x89PNG\r\n\x1a\n'

class Latex(commands.Cog):
    @commands.cooldown(rate=2, per=20.0, type=commands.BucketType.user)
    @commands.command(brief=messages.latex_desc, description=messages.latex_help)
    async def latex(self, ctx, *, equation):
        channel = ctx.channel
        async with ctx.typing():
            eq = urllib.parse.quote(equation)
            imgURL = f"http://www.sciweavers.org/tex2img.php?eq={eq}&fc=White&im=png&fs=25&edit=0"

            async with aiohttp.ClientSession() as session:
                async with session.get(imgURL) as resp:

                    if resp.status != 200:
                        return await ctx.send("Could not get image.")

                    data = await resp.read()
                    if not data.startswith(PNG_HEADER):
                        return await ctx.send("Could not get image.")

                    datastream = io.BytesIO(data)
                    await channel.send(file=discord.File(datastream, "latex.png"))


def setup(bot):
    bot.add_cog(Latex(bot))
