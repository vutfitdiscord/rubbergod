import traceback

import disnake
from disnake.ext import commands
import sqlalchemy

from repository.database import session
from config.app_config import config
from config.messages import Messages
import utils


class Error(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        # The local handlers so far only catch bad arguments so we still
        # want to print the rest
        if isinstance(error, disnake.errors.DiscordServerError):
            return
        if isinstance(error, sqlalchemy.exc.InternalError):
            session.rollback()
            return
        if (
            isinstance(error, commands.BadArgument)
            or isinstance(error, commands.errors.CheckFailure)
            or isinstance(error, commands.errors.MissingAnyRole)
            or isinstance(error, commands.errors.MissingRequiredArgument)
        ) and hasattr(ctx.command, "on_error"):
            return

        if isinstance(error, commands.UserInputError):
            await ctx.send("Chyba ve vstupu, jestli vstup obsahuje `\"` nahraď je za `'`")
            return

        if isinstance(error, commands.CommandNotFound):
            slash_comms = [command.name for command in self.bot.slash_commands]
            invoked = ctx.message.content.split(" ")[0][1:]
            prefix = ctx.message.content[:1]
            
            if invoked in slash_comms:
                await ctx.reply(utils.fill_message("moved_command", invoked=invoked))
            elif prefix not in config.ignored_prefixes:
                await ctx.send(Messages.no_such_command)
            return

        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(utils.fill_message("spamming", user=ctx.author.id))
            return

        if isinstance(error, utils.NotHelperPlusError):
            await ctx.send(Messages.helper_plus_only)
            return

        output = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        embed = disnake.Embed(title=f"Ignoring exception in command {ctx.command}", color=0xFF0000)
        embed.add_field(name="Zpráva", value=ctx.message.content[:1000])
        embed.add_field(name="Autor", value=str(ctx.author))
        if ctx.guild and ctx.guild.id != config.guild_id:
            embed.add_field(name="Guild", value=ctx.guild.name)
        embed.add_field(name="Link", value=ctx.message.jump_url, inline=False)
        
        channel = self.bot.get_channel(config.bot_dev_channel)

        output = utils.cut_string(output, 1900)
        if channel is not None:
            for message in output:
                await channel.send(f"```\n{message}\n```")

    @commands.Cog.listener()
    async def on_slash_command_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, disnake.errors.DiscordServerError):
            return

        if isinstance(error, sqlalchemy.exc.InternalError):
            session.rollback()
            return
        
        if isinstance(error, disnake.InteractionTimedOut):
            await inter.response.send_message(Messages.command_timed_out)
            return

        if isinstance(error, commands.CommandOnCooldown):
            await inter.response.send_message(utils.fill_message("spamming", user=inter.author.id))
            return

        url = f"https://discord.com/channels/{inter.guild_id}/{inter.channel_id}/{inter.id}"

        output = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        embed = disnake.Embed(title=f"Ignoring exception in command {inter.data.name}", color=0xFF0000)
        embed.add_field(name="Zpráva", value=inter.filled_options)
        embed.add_field(name="Autor", value=str(inter.author))
        if inter.guild and inter.guild.id != config.guild_id:
            embed.add_field(name="Guild", value=inter.guild.name)
        embed.add_field(name="Link", value=url, inline=False)
        
        channel = self.bot.get_channel(config.bot_dev_channel)

        # send context of command with personal information to DM
        if inter.data.name == "diplom":
            channel_ctx = self.bot.get_user(config.admin_ids[0])
        else:
            channel_ctx = channel
        await channel_ctx.send(embed=embed)

        output = utils.cut_string(output, 1900)
        if channel is not None:
            for message in output:
                await channel.send(f"```\n{message}\n```")

def setup(bot):
    bot.add_cog(Error(bot))
