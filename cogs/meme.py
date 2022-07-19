import datetime
from io import BytesIO
from PIL import Image, ImageDraw
from random import choice
import requests
from typing import List

import disnake
from disnake.ext import commands

import utils
from config.app_config import config
from config.messages import Messages
from config import cooldowns

uhoh_counter = 0
storno_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=config.storno_delay)
storno_images = ["storno.png", "storno_lgtm.png"]


class Meme(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: disnake.message):
        global uhoh_counter
        global storno_time

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
        elif (
            storno_time + datetime.timedelta(hours=config.storno_delay)
            < message.created_at
            and "storno" in message.content.lower()
            and message.channel.id == config.covid_channel_id
        ):
            storno_time = message.created_at
            image = choice(storno_images)
            await message.channel.send(
                utils.fill_message("covid_storno", user=message.author.id),
                file=disnake.File(f"images/{image}", filename=image),
            )

    @commands.command(brief=Messages.uhoh_brief)
    async def uhoh(self, ctx):
        await ctx.send(utils.fill_message("uhoh_counter", uhohs=uhoh_counter))

    @cooldowns.short_cooldown
    @commands.command(name="??", brief="???")
    async def question(self, ctx):
        await ctx.send(choice(Messages.question))

    @cooldowns.short_cooldown
    @commands.command(brief=Messages.bonk_brief)
    async def bonk(self, ctx, member: disnake.Member = None):
        """Bonk someone
        member: disnake user. If none, the bot will bonk you.
        """
        if member is None:
            bonked = ctx.author
        else:
            bonked = member

        async with ctx.typing():
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
                await ctx.reply(
                    file=disnake.File(fp=image_binary, filename="bonk.gif"),
                    mention_author=False,
                )

    def get_bonk_frames(self, avatar: Image.Image) -> List[Image.Image]:
        """Get frames for the bonk"""
        frames = []
        width, height = 200, 170
        deformation = (0, 0, 0, 5, 10, 20, 15, 5)

        avatar = self.round_image(avatar.resize((100, 100)))

        for i in range(8):
            img = "%02d" % (i + 1)
            frame = Image.new("RGBA", (width, height), (54, 57, 63, 1))
            bat = Image.open(f"images/bonk/{img}.png")

            frame_avatar = avatar.resize((100, 100 - deformation[i]))

            frame.paste(frame_avatar, (80, 60 + deformation[i]), frame_avatar)
            frame.paste(bat, (10, 5), bat)
            frames.append(frame)

        return frames

    @staticmethod
    def round_image(frame_avatar: Image.Image) -> Image.Image:
        """Convert square avatar to circle"""
        frame_mask = Image.new("1", frame_avatar.size, 0)
        draw = ImageDraw.Draw(frame_mask)
        draw.ellipse((0, 0) + frame_avatar.size, fill=255)
        frame_avatar.putalpha(frame_mask)
        return frame_avatar

    @bonk.error
    async def bonk_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(utils.fill_message("member_not_found", user=ctx.author.id))


def setup(bot):
    bot.add_cog(Meme(bot))
