"""
Cog for handling command errors. This is mostly for logging purposes.
Errors originating from other than commands (such as reaction handlers and listeners)
are handled in rubbergod.py `on_error` function.

Listeners catch errors from commands and send a response to the user.
If an error remains uncaught, the entire traceback is printed to the bot_dev_channel.
"""

from io import BytesIO

import disnake
from disnake.ext import commands

from cogs.base import Base
from database.stats import ErrorEvent
from features.error import ErrorLogger


class Error(Base, commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
        self.logger = ErrorLogger(bot)

    @commands.Cog.listener()
    async def on_button_click(self, inter: disnake.MessageInteraction):
        if inter.component.custom_id != "error:traceback":
            return
        await inter.response.defer(ephemeral=True)
        id = inter.message.embeds[0].footer.text.split(":")[1].strip()
        traceback = ErrorEvent.get_traceback(id).traceback
        with BytesIO(bytes(traceback, 'utf-8')) as file_binary:
            file = disnake.File(fp=file_binary, filename="traceback.txt")
        await inter.send(file=file)

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


def setup(bot: commands.Bot):
    bot.add_cog(Error(bot))
