import datetime
import traceback

import discord
from discord.ext import commands

import utils
from config import app_config as config, messages
from repository import karma_repo
from cogs import room_check

config = config.Config
messages = messages.Messages
karma_r = karma_repo.KarmaRepository()

boottime = datetime.datetime.now().replace(microsecond=0)


class Base(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check = room_check.RoomCheck(bot)

    @commands.cooldown(rate=2, per=20.0, type=commands.BucketType.user)
    @commands.command()
    async def uptime(self, ctx):
        now = datetime.datetime.now().replace(microsecond=0)
        delta = now - boottime
        await ctx.send(utils.fill_message("uptime_message", boottime=str(boottime), uptime=str(delta)))

    def make_embed(self, page):
        embed = discord.Embed(title="Rubbergod",
                              description="Nejlepší a nejúžasnější bot ever.",
                              color=0xeee657)

        prefix = config.default_prefix

        embed.add_field(name="Autor", value="Toaster#1111")

        # Shows the number of servers the bot is member of.
        embed.add_field(name="Počet serverů s touto instancí bota",
                        value=f"{len(self.bot.guilds)}")

        embed.add_field(name="\u200b", value="Příkazy:", inline=False)

        info = messages.info[page - 1]

        for command in info:
            embed.add_field(name=prefix + command[0],
                            value=command[1],
                            inline=False)

        git_hash = utils.git_hash()
        footer_text = f"Commit {git_hash}"

        if len(messages.info) > 1:
            footer_text = f"Page {page} | {footer_text}"

        embed.set_footer(text=footer_text, icon_url=self.bot.user.avatar_url)
        return embed


def setup(bot):
    bot.add_cog(Base(bot))
