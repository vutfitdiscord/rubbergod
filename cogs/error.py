import traceback

import discord
from discord.ext import commands

from config import app_config as config, messages
import utils


class Error(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        # The local handlers so far only catch bad arguments so we still
        # want to print the rest
        if (
            isinstance(error, commands.BadArgument)
            or isinstance(error, commands.errors.CheckFailure)
            or isinstance(error, commands.errors.MissingAnyRole)
            or isinstance(error, commands.errors.MissingRequiredArgument)
        ) and hasattr(ctx.command, "on_error"):
            return

        if isinstance(error, commands.UserInputError):
            await ctx.send("Chyba ve vstupu")
            return

        if isinstance(error, commands.CommandNotFound):
            prefix = ctx.message.content[:1]
            if prefix not in config.Config.ignored_prefixes:
                await ctx.send(messages.Messages.no_such_command)
            return

        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(utils.fill_message("spamming", user=ctx.author.id))
            return

        if isinstance(error, utils.NotHelperPlusError):
            await ctx.send(messages.Messages.helper_plus_only)
            return

        output = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        embed = discord.Embed(title=f"Ignoring exception in command {ctx.command}", color=0xFF0000)
        embed.add_field(name="Zpráva", value=ctx.message.content[:1000])
        embed.add_field(name="Autor", value=str(ctx.author))
        if ctx.guild.id != config.Config.guild_id:
            embed.add_field(name="Guild", value=ctx.guild.name)
        embed.add_field(name="Link", value=ctx.message.jump_url, inline=False)
        channel = self.bot.get_channel(config.Config.bot_dev_channel)
        print(output)
        await channel.send(embed=embed)
        output = utils.cut_string(output, 1900)
        if channel is not None:
            for message in output:
                await channel.send(f"```\n{message}\n```")


def setup(bot):
    bot.add_cog(Error(bot))
