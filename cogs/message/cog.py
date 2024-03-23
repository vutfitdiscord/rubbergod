"""
Cog for sending and managing messages sent by bot.
"""

import disnake
from disnake.ext import commands

from cogs.base import Base
from config import cooldowns
from permissions import permission_check

from .messages_cz import MessagesCZ
from .modals import Modal


class Message(Base, commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    @commands.check(permission_check.submod_plus)
    @cooldowns.default_cooldown
    @commands.slash_command(name="message")
    async def message(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @message.sub_command(name="send", description=MessagesCZ.send_brief)
    async def send(
        self,
        inter: disnake.ApplicationCommandInteraction,
        channel: disnake.TextChannel = commands.Param(description=MessagesCZ.channel_param),
    ):
        message_modal = Modal(self.bot, title="Send message", channel=channel)
        await inter.response.send_modal(modal=message_modal)

    @message.sub_command(name="resend", description=MessagesCZ.resend_brief)
    async def resend(
        self,
        inter: disnake.ApplicationCommandInteraction,
        channel: disnake.TextChannel = commands.Param(description=MessagesCZ.channel_param),
        message_url: str = commands.Param(description=MessagesCZ.url_param),
    ):
        try:
            message: disnake.Message = await commands.MessageConverter().convert(inter, message_url)
        except commands.MessageNotFound:
            await inter.send(MessagesCZ.message_not_found, ephemeral=True)
            return
        if len(message.content) > 2000:
            await inter.send(MessagesCZ.message_too_long, ephemeral=True)
            return
        await inter.send(MessagesCZ.message_sent(channel=channel.mention), ephemeral=True)
        await channel.send(message.content)

    @message.sub_command(name="edit", description=MessagesCZ.edit_brief)
    async def edit(
        self,
        inter: disnake.ApplicationCommandInteraction,
        message_url: str = commands.Param(description=MessagesCZ.url_param),
    ):
        try:
            message: disnake.Message = await commands.MessageConverter().convert(inter, message_url)
        except commands.MessageNotFound:
            await inter.send(MessagesCZ.message_not_found, ephemeral=True)
            return
        if len(message.content) > 2000:
            await inter.send(MessagesCZ.message_too_long, ephemeral=True)
            return
        message_modal = Modal(self.bot, title="Edit message", message=message, edit=True)
        await inter.response.send_modal(modal=message_modal)
