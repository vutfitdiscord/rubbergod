"""
Cog for sending and managing messages sent by bot.
"""

import disnake
from disnake.ext import commands

import utils
from cogs.base import Base
from rubbergod import Rubbergod
from utils import cooldowns
from utils.checks import PermissionsCheck

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
        embed = disnake.Embed(title="🔁 Message resent", color=disnake.Color.green())
        embed.add_field(name="Target channel", value=sent_message.channel.mention, inline=False)
        embed.add_field(
            name="New message link", value=f"[Jump to message]({sent_message.jump_url})", inline=False
        )
        embed.add_field(
            name="Original message", value=f"[Jump to original]({original_message.jump_url})", inline=False
        )

        content_preview = (
            sent_message.content[:100] + "..." if len(sent_message.content) > 100 else sent_message.content
        )
        if content_preview:
            embed.add_field(name="Content preview", value=content_preview, inline=False)

        if sent_message.attachments:
            embed.add_field(
                name="Attachments", value=f"{len(sent_message.attachments)} file(s)", inline=False
            )

        utils.embed.add_author_footer(embed, inter.author)
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
