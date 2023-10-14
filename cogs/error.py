"""
Cog for handling command errors. This is mostly for logging purposes.
Errors originating from other than commands (such as reaction handlers and listeners)
are handled in rubbergod.py `on_error` function.

Listeners catch errors from commands and send a response to the user.
If an error remains uncaught, the entire traceback is printed to the bot_dev_channel.

CheckFailure must be last in the list of errors, because it is the most generic one.
"""

import traceback
from datetime import datetime, timedelta

import disnake
import sqlalchemy
from disnake.ext import commands

import utils
from cogs.base import Base
from config.messages import Messages
from database import session
from features.error import ErrorLogger
from permissions import permission_check


class Error(Base, commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.logger = ErrorLogger()

    def create_error_embed(
        self,
        inter: disnake.ApplicationCommandInteraction,
        prefix: str,
        filled_options=None
    ):
        filled_options = filled_options or inter.filled_options
        embed = self.logger.create_embed(
            f"{prefix}{inter.application_command.qualified_name}",
            filled_options,
            inter.author,
            inter.guild,
            f"https://discord.com/channels/{inter.guild_id}/{inter.channel_id}/{inter.id}",
        )
        return embed

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
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

        if (
            isinstance(error, commands.BadArgument)
            or isinstance(error, commands.MissingAnyRole)
            or isinstance(error, commands.MissingRequiredArgument)
        ) and hasattr(ctx.command, "on_error"):
            return

        if isinstance(error, commands.UserInputError):
            await ctx.send(Messages.user_input_error)
            return

        if isinstance(error, commands.UserNotFound):
            await ctx.send(Messages.user_not_found(user=ctx.author.mention))
            return

        if isinstance(error, commands.MemberNotFound):
            await ctx.send(Messages.member_not_found(member=ctx.author.mention))
            return

        if isinstance(error, commands.CommandNotFound):
            slash_comms = [command.name for command in self.bot.slash_commands]
            invoked = ctx.message.content.split(" ")[0][1:]
            prefix = ctx.message.content[:1]

            if invoked in slash_comms:
                command_id = utils.get_command_id(self, invoked)
                await ctx.reply(Messages.moved_command(name=invoked, id=command_id))
            elif prefix not in self.config.ignored_prefixes:
                await ctx.send(Messages.no_such_command)
            return

        if isinstance(error.original, disnake.errors.Forbidden):
            # bot cant send messages to user
            await ctx.channel.send(Messages.blocked_bot(user=ctx.author.id))
            return

        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(Messages.command_invoke_error)
            # no return here, because we want to log these errors

        if isinstance(error, commands.CommandOnCooldown):
            time = datetime.now() + timedelta(seconds=error.retry_after)
            retry_after = utils.get_discord_timestamp(time, style="Relative Time")
            await ctx.send(Messages.spamming(user=ctx.author.id, time=retry_after))
            return

        if isinstance(error, commands.NoPrivateMessage):
            await ctx.send(Messages.guild_only)
            return

        if isinstance(error, commands.CheckFailure):
            await ctx.reply(Messages.missing_perms(user=ctx.author.id))
            return

        output = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        embed = self.logger.create_embed(
            ctx.command,
            ctx.message.content[:1000],
            ctx.author,
            ctx.guild,
            ctx.message.jump_url
        )

        await self.bot_dev_channel.send(embed=embed)

        await self.logger.send_output(output, self.bot_dev_channel)

    @commands.Cog.listener()
    async def on_slash_command_error(self, inter: disnake.ApplicationCommandInteraction, error):
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
            await inter.send(error.message)
            return

        if isinstance(error, commands.UserNotFound):
            await inter.send(Messages.user_not_found(user=inter.author.mention))
            return

        if isinstance(error, commands.MemberNotFound):
            await inter.send(Messages.member_not_found(member=inter.author.mention))
            return

        if hasattr(error, "original"):
            if isinstance(error.original, disnake.errors.InteractionTimedOut):
                embed = self.create_error_embed(inter, "/", "Interaction timed out")
                await self.bot_dev_channel.send(embed=embed)
                return

            if isinstance(error.original, disnake.errors.Forbidden):
                # bot cant send messages to user
                if error.original.code == 50007:
                    await inter.channel.send(Messages.blocked_bot(user=inter.author.id))
                    return

        if isinstance(error, commands.CommandInvokeError):
            await inter.send(Messages.command_invoke_error)
            # no return here, because we want to log these errors

        if isinstance(error, commands.CommandOnCooldown):
            time = datetime.now() + timedelta(seconds=error.retry_after)
            retry_after = utils.get_discord_timestamp(time, style="Relative Time")
            await inter.send(
                Messages.spamming(user=inter.author.id, time=retry_after),
                ephemeral=True
            )
            return

        if isinstance(error, commands.NoPrivateMessage):
            await inter.send(Messages.guild_only)
            return

        if isinstance(error, commands.CheckFailure):
            await inter.send(
                Messages.missing_perms(user=inter.author.id),
                ephemeral=True
            )
            return

        embed = self.logger.create_embed(
            f"/{inter.application_command.qualified_name}",
            inter.filled_options,
            inter.author,
            inter.guild,
            f"https://discord.com/channels/{inter.guild_id}/{inter.channel_id}/{inter.id}",
        )

        # send context of command with personal information to DM
        if inter.data.name == "diplom":
            channel_ctx = self.bot.get_user(self.config.admin_ids[0])
        else:
            channel_ctx = self.bot_dev_channel
        await channel_ctx.send(embed=embed)

        output = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        await self.logger.send_output(output, self.bot_dev_channel)

    @commands.Cog.listener()
    async def on_user_command_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if (
            isinstance(error, permission_check.NotHelperPlusError)
            or isinstance(error, permission_check.NotSubmodPlusError)
            or isinstance(error, permission_check.NotModPlusError)
            or isinstance(error, permission_check.NotAdminError)
        ):
            await inter.send(error.message)
            return

        if isinstance(error, commands.UserNotFound):
            await inter.send(Messages.user_not_found(user=inter.author.mention))
            return

        if isinstance(error, commands.MemberNotFound):
            await inter.send(Messages.member_not_found(member=inter.author.mention))
            return

        if hasattr(error, "original"):
            if hasattr(error, "original") and isinstance(error.original, disnake.errors.InteractionTimedOut):
                embed = self.create_error_embed(inter, "User command - ", "Interaction timed out")
                await self.bot_dev_channel.send(embed=embed)
                return

            if isinstance(error.original, disnake.errors.Forbidden):
                # bot cant send messages to user
                if error.original.code == 50007:
                    await inter.channel.send(Messages.blocked_bot(user=inter.author.id))
                    return

        if isinstance(error, commands.CommandInvokeError):
            await inter.send(Messages.command_invoke_error)
            # no return here, because we want to log these errors

        if isinstance(error, commands.CommandOnCooldown):
            time = datetime.now() + timedelta(seconds=error.retry_after)
            retry_after = utils.get_discord_timestamp(time, style="Relative Time")
            await inter.send(
                Messages.spamming(user=inter.author.id, time=retry_after),
                ephemeral=True
            )
            return
        if isinstance(error, commands.CheckFailure):
            await inter.send(Messages.missing_perms(user=inter.author.id))
            return

        embed = self.logger.create_embed(
            f"User command - {inter.application_command.qualified_name}",
            inter.filled_options,
            inter.author,
            inter.guild,
            f"https://discord.com/channels/{inter.guild_id}/{inter.channel_id}/{inter.id}",
        )

        await self.bot_dev_channel.send(embed=embed)

        output = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        await self.logger.send_output(output, self.bot_dev_channel)

    @commands.Cog.listener()
    async def on_message_command_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if (
            isinstance(error, permission_check.NotHelperPlusError)
            or isinstance(error, permission_check.NotSubmodPlusError)
            or isinstance(error, permission_check.NotModPlusError)
            or isinstance(error, permission_check.NotAdminError)
        ):
            await inter.send(error.message)
            return

        if hasattr(error, "original"):
            if isinstance(error.original, disnake.errors.InteractionTimedOut):
                embed = self.create_error_embed(inter, "Message command - ", "Interaction timed out")
                await self.bot_dev_channel.send(embed=embed)
                return

            if isinstance(error.original, disnake.errors.Forbidden):
                # bot cant send messages to user
                if error.original.code == 50007:
                    await inter.channel.send(Messages.blocked_bot(user=inter.author.id))
                    return

        if isinstance(error, commands.CommandInvokeError):
            await inter.send(Messages.command_invoke_error)
            # no return here, because we want to log these errors

        if isinstance(error, commands.CommandOnCooldown):
            time = datetime.now() + timedelta(seconds=error.retry_after)
            retry_after = utils.get_discord_timestamp(time, style="Relative Time")
            await inter.send(
                Messages.spamming(user=inter.author.id, time=retry_after),
                ephemeral=True
            )
            return

        if isinstance(error, commands.CheckFailure):
            await inter.send(Messages.missing_perms(user=inter.author.id))
            return

        embed = self.logger.create_embed(
            f"Message command - {inter.application_command.qualified_name}",
            inter.filled_options,
            inter.author,
            inter.guild,
            f"https://discord.com/channels/{inter.guild_id}/{inter.channel_id}/{inter.id}",
        )

        await self.bot_dev_channel.send(embed=embed)

        output = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        await self.logger.send_output(output, self.bot_dev_channel)


def setup(bot):
    bot.add_cog(Error(bot))
