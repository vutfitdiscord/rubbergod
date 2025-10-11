"""
Cog for sending and managing messages sent by bot.
"""

import disnake
from disnake.ext import commands

from cogs.base import Base
from rubbergod import Rubbergod
from utils import cooldowns
from utils.checks import PermissionsCheck
from utils.general import get_content_preview

from .features import create_message_log_embed
from .messages_cz import MessagesCZ
from .modals import MessageModal


class Message(Base, commands.Cog):
    def __init__(self, bot: Rubbergod):
        super().__init__()
        self.bot = bot

    @PermissionsCheck.is_submod_plus()
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
        if not attachment:
            message_modal = MessageModal(self.bot, title="Send message", files=[], channel=channel)
            await inter.response.send_modal(modal=message_modal)
            return

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
        sent_message = await channel.send(message_url.content, files=files)
        await self._log_resend(inter, sent_message, message_url)

    async def _log_resend(
        self,
        inter: disnake.ApplicationCommandInteraction,
        sent_message: disnake.Message,
        original_message: disnake.Message,
    ) -> None:
        """Log message resend operation to log channel"""
        content_preview = get_content_preview(sent_message.content)
        attachments_count = len(sent_message.attachments) if sent_message.attachments else None

        additional_fields = [("Original message", f"[Jump to original]({original_message.jump_url})")]

        embed = await create_message_log_embed(
            title="🔁 Message resent",
            color=disnake.Color.green(),
            channel=sent_message.channel,
            message_link=sent_message.jump_url,
            content_preview=content_preview,
            attachments_count=attachments_count,
            author=inter.author,
            additional_fields=additional_fields,
        )

        await self.log_channel.send(embed=embed)

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
