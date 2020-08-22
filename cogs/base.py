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

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        # The local handlers so far only catch bad arguments so we still
        # want to print the rest
        if (isinstance(error, commands.BadArgument) or
           isinstance(error, commands.errors.CheckFailure) or
           isinstance(error, commands.errors.MissingAnyRole) or
           isinstance(error, commands.errors.MissingRequiredArgument)) and \
           hasattr(ctx.command, 'on_error'):
            return

        if isinstance(error, commands.UserInputError):
            await ctx.send("Chyba ve vstupu")
            return

        if isinstance(error, commands.CommandNotFound):
            prefix = ctx.message.content[:1]
            if prefix not in config.ignored_prefixes:
                await ctx.send(messages.no_such_command)
            return

        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(utils.fill_message("spamming", user=ctx.author.id))
            return

        if isinstance(error, utils.NotHelperPlusError):
            await ctx.send(messages.helper_plus_only)
            return

        output = "Ignoring exception in command {}:\n".format(ctx.command)
        output += "".join(traceback.format_exception(type(error), error, error.__traceback__))
        channel = self.bot.get_channel(config.bot_dev_channel)
        print(output)
        output = utils.cut_string(output, 1900)
        if channel is not None:
            for message in output:
                await channel.send("```\n" + message + "\n```")

    @commands.cooldown(rate=2, per=20.0, type=commands.BucketType.user)
    @commands.command()
    async def uptime(self, ctx):
        now = datetime.datetime.now().replace(microsecond=0)
        delta = now - boottime
        await ctx.send(utils.fill_message("uptime_message", boottime=str(boottime), uptime=str(delta)))

    @commands.cooldown(rate=2, per=60.0, type=commands.BucketType.user)
    @commands.command(aliases=["help"])
    async def god(self, ctx):
        embed = self.make_embed(1)

        channel = await self.check.get_room(ctx.message)
        if channel is not None and channel.id != config.bot_room:
            try:
                msg = await ctx.author.send(embed=embed)
                await ctx.message.delete()
            except discord.errors.Forbidden:
                return
        else:
            msg = await ctx.send(embed=embed)

        if len(messages.info) > 1:
            await msg.add_reaction("◀")
            await msg.add_reaction("▶")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        ctx = await utils.reaction_get_ctx(self.bot, payload)
        if ctx is None:
            return

        if ctx['message'].embeds and ctx['message'].embeds[0].title == "Rubbergod":
            if ctx['emoji'] in ["◀", "▶"]:
                page = int(ctx['message'].embeds[0].footer.text[5])
                next_page = utils.pagination_next(ctx['emoji'], page, len(messages.info))
                if next_page:
                    embed = self.make_embed(next_page)
                    await ctx['message'].edit(embed=embed)
            if ctx['message'].guild: 
                await ctx['message'].remove_reaction(ctx['emoji'], ctx['member'])

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
