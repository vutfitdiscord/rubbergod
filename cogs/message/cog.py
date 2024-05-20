"""
Cog for sending and managing messages sent by bot.
"""

import disnake
from disnake.ext import commands

from cogs.base import Base
from config import cooldowns
from permissions import permission_check

from .messages_cz import MessagesCZ
from .modals import MessageModal


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
        attachment: disnake.Attachment = commands.Param(
            default=None, description=MessagesCZ.attachment_param
        ),
    ):
        if attachment.size > 25_000_000:
            await inter.send(MessagesCZ.attachment_too_big, ephemeral=True)
            return
        file = await attachment.to_file()
        message_modal = MessageModal(self.bot, title="Send message", files=[file], channel=channel)
        await inter.response.send_modal(modal=message_modal)

    @message.sub_command(name="resend", description=MessagesCZ.resend_brief)
    async def resend(
        self,
        inter: disnake.ApplicationCommandInteraction,
        channel: disnake.TextChannel = commands.Param(description=MessagesCZ.channel_param),
        message_url: disnake.Message = commands.Param(description=MessagesCZ.url_param),
    ):
        if len(message_url.content) > 2000:
            await inter.send(MessagesCZ.message_too_long, ephemeral=True)
            return

        files = [await attachment.to_file() for attachment in message_url.attachments]
        await inter.send(MessagesCZ.message_sent(channel=channel.mention), ephemeral=True)
        await channel.send(message_url.content, files=files)

    @message.sub_command(name="edit", description=MessagesCZ.edit_brief)
    async def edit(
        self,
        inter: disnake.ApplicationCommandInteraction,
        message_url: disnake.Message = commands.Param(description=MessagesCZ.url_param),
    ):
        if len(message_url.content) > 2000:
            await inter.send(MessagesCZ.message_too_long, ephemeral=True)
            return
        message_modal = MessageModal(self.bot, title="Edit message", message=message_url, edit=True)
        await inter.response.send_modal(modal=message_modal)
