import datetime
from random import choice

import discord
from discord.ext import commands

import utils
from config import app_config as config, messages

config = config.Config
messages = messages.Messages

uhoh_counter = 0
storno_time = datetime.datetime.utcnow() - datetime.timedelta(hours=config.storno_delay)
storno_images = ["storno.png", "storno_lgtm.png"]


class Meme(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.message):
        global uhoh_counter
        global storno_time

        if message.author.bot:
            if (
                message.author.id == config.grillbot_id
                and message.content.startswith("<:")
                and message.content.endswith(">")
            ):
                await message.channel.send(message.content)
            return

        elif config.uhoh_string in message.content.lower():
            await message.channel.send("uh oh")
            uhoh_counter += 1
        elif message.content == "PR":
            await message.channel.send(messages.pr_meme)
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
                file=discord.File(f"images/{image}", filename=image),
            )

    @commands.command(brief=messages.uhoh_brief)
    async def uhoh(self, ctx):
        await ctx.send(utils.fill_message("uhoh_counter", uhohs=uhoh_counter))

    @commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)
    @commands.command(name="??", brief="???")
    async def question(self, ctx):
        await ctx.send(choice(messages.question))


def setup(bot):
    bot.add_cog(Meme(bot))
