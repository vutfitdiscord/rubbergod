import traceback

import disnake
from disnake.ext import commands
import sqlalchemy

from config.app_config import config
from config.messages import Messages
from features.error import ErrorLogger
from repository.database import session
import utils
from permissions import permission_check


class Error(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = ErrorLogger()

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
            isinstance(error, permission_check.NotHelperPlusError)
            or isinstance(error, permission_check.NotSubmodPlusError)
            or isinstance(error, permission_check.NotModPlusError)
            or isinstance(error, permission_check.NotAdminError)
        ):
            await ctx.send(error.message)
            return
        if isinstance(error, commands.errors.CheckFailure):
            await ctx.reply(utils.fill_message("missing_perms", user=ctx.author.id))
            return
        if (
            isinstance(error, commands.BadArgument)
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
                command_id = utils.get_command_id(self, invoked)
                await ctx.reply(utils.fill_message("moved_command", name=invoked, id=command_id))
            elif prefix not in config.ignored_prefixes:
                await ctx.send(Messages.no_such_command)
            return

        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(utils.fill_message("spamming", user=ctx.author.id, time=error.retry_after))
            return

        if isinstance(error, commands.NoPrivateMessage):
            await ctx.send(Messages.guild_only)
            return

        output = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        embed = self.logger.create_embed(
            ctx.command,
            ctx.message.content[:1000],
            ctx.author,
            ctx.guild,
            ctx.message.jump_url
        )

        channel = self.bot.get_channel(config.bot_dev_channel)
        await channel.send(embed=embed)

        await self.logger.send_output(output, channel)

    @commands.Cog.listener()
    async def on_slash_command_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, disnake.errors.DiscordServerError):
            return

        if (
            isinstance(error, permission_check.NotHelperPlusError)
            or isinstance(error, permission_check.NotSubmodPlusError)
            or isinstance(error, permission_check.NotModPlusError)
            or isinstance(error, permission_check.NotAdminError)
        ):
            await inter.response.send_message(error.message)
            return

        if isinstance(error, commands.errors.CheckFailure):
            await inter.response.send_message(utils.fill_message("missing_perms", user=inter.author.id))
            return

        if isinstance(error, sqlalchemy.exc.InternalError):
            session.rollback()
            return

        if isinstance(error, disnake.InteractionTimedOut):
            await inter.response.send_message(Messages.command_timed_out)
            return

        if isinstance(error, commands.CommandOnCooldown):
            await inter.response.send_message(
                utils.fill_message("spamming", user=inter.author.id, time=error.retry_after)
            )
            return

        embed = self.logger.create_embed(
            f"/{inter.application_command.qualified_name}",
            inter.filled_options,
            inter.author,
            inter.guild,
            f"https://discord.com/channels/{inter.guild_id}/{inter.channel_id}/{inter.id}",
        )

        channel = self.bot.get_channel(config.bot_dev_channel)

        # send context of command with personal information to DM
        if inter.data.name == "diplom":
            channel_ctx = self.bot.get_user(config.admin_ids[0])
        else:
            channel_ctx = channel
        await channel_ctx.send(embed=embed)

        output = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        await self.logger.send_output(output, channel)

    @commands.Cog.listener()
    async def on_user_command_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if (
            isinstance(error, permission_check.NotHelperPlusError)
            or isinstance(error, permission_check.NotSubmodPlusError)
            or isinstance(error, permission_check.NotModPlusError)
            or isinstance(error, permission_check.NotAdminError)
        ):
            await inter.response.send_message(error.message)
            return
        if isinstance(error, commands.errors.CheckFailure):
            await inter.response.send_message(utils.fill_message("missing_perms", user=inter.author.id))
            return

    @commands.Cog.listener()
    async def on_message_command_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if (
            isinstance(error, permission_check.NotHelperPlusError)
            or isinstance(error, permission_check.NotSubmodPlusError)
            or isinstance(error, permission_check.NotModPlusError)
            or isinstance(error, permission_check.NotAdminError)
        ):
            await inter.response.send_message(error.message)
            return
        if isinstance(error, commands.errors.CheckFailure):
            await inter.response.send_message(utils.fill_message("missing_perms", user=inter.author.id))
            return


def setup(bot):
    bot.add_cog(Error(bot))
