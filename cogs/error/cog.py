"""
Cog for handling command errors. This is mostly for logging purposes.
Errors originating from other than commands (such as reaction handlers and listeners)
are handled in rubbergod.py `on_error` function.

Listeners catch errors from commands and send a response to the user.
If an error remains uncaught, the entire traceback is printed to the bot_dev_channel.
"""

import disnake
from disnake.ext import commands

from cogs.base import Base
from features.error import ErrorLogger


class Error(Base, commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
        self.logger = ErrorLogger(bot)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Exception):
        await self.logger.handle_error(ctx, error)

    @commands.Cog.listener()
    async def on_slash_command_error(self, inter: disnake.ApplicationCommandInteraction, error: Exception):
        await self.logger.handle_error(inter, error)

    @commands.Cog.listener()
    async def on_user_command_error(self, inter: disnake.ApplicationCommandInteraction, error: Exception):
        await self.logger.handle_error(inter, error)

    @commands.Cog.listener()
    async def on_message_command_error(self, inter: disnake.ApplicationCommandInteraction, error: Exception):
        await self.logger.handle_error(inter, error)
