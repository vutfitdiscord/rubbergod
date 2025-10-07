import disnake

import utils
from config.app_config import config

from .messages_cz import MessagesCZ


class MessageModal(disnake.ui.Modal):
    def __init__(
        self,
        bot,
        title: str,
        channel: disnake.TextChannel = None,
        message: disnake.Message = None,
        files: list[disnake.File] = None,
        edit: bool = False,
    ) -> None:
        self.bot = bot
        self.title = title
        self.channel = channel
        self.message = message
        self.files = files
        self.edit = edit
        components = [
            disnake.ui.TextInput(
                label="Message content",
                custom_id="content",
                style=disnake.TextInputStyle.long,
                required=False if files else True,
                value=message.content if message and edit else None,
                max_length=2000,
            )
        ]

        super().__init__(title=self.title, custom_id="message_modal", timeout=900, components=components)

    async def callback(self, inter: disnake.ModalInteraction) -> None:
        if self.edit and self.message:
            await self.message.edit(inter.text_values["content"])
            await inter.send(MessagesCZ.message_sent(channel=self.message.channel.mention), ephemeral=True)
            await self._log_edit(inter)
            return

        if self.channel:
            content = inter.text_values["content"] or None
            sent_message = await self.channel.send(content, files=self.files)
            await inter.send(MessagesCZ.message_sent(channel=self.channel.mention), ephemeral=True)
            await self._log_send(inter, sent_message)

    async def _log_send(self, inter: disnake.ModalInteraction, sent_message: disnake.Message) -> None:
        """Log message send operation to log channel"""
        embed = disnake.Embed(title="📤 Message sent", color=disnake.Color.blue())
        embed.add_field(name="Channel", value=self.channel.mention, inline=False)
        embed.add_field(
            name="Message link", value=f"[Jump to message]({sent_message.jump_url})", inline=False
        )

        content_preview = (
            sent_message.content[:100] + "..." if len(sent_message.content) > 100 else sent_message.content
        )
        if content_preview:
            embed.add_field(name="Content preview", value=content_preview, inline=False)

        if self.files:
            embed.add_field(name="Attachments", value=f"{len(self.files)} file(s)", inline=False)

        utils.embed.add_author_footer(embed, inter.author)

        log_channel = self.bot.get_channel(config.log_channel)
        await log_channel.send(embed=embed)

    async def _log_edit(self, inter: disnake.ModalInteraction) -> None:
        """Log message edit operation to log channel"""
        embed = disnake.Embed(title="✏️ Message edited", color=disnake.Color.orange())
        embed.add_field(name="Channel", value=self.message.channel.mention, inline=False)
        embed.add_field(
            name="Message link", value=f"[Jump to message]({self.message.jump_url})", inline=False
        )

        content_preview = (
            self.message.content[:100] + "..." if len(self.message.content) > 100 else self.message.content
        )
        if content_preview:
            embed.add_field(name="New content preview", value=content_preview, inline=False)

        utils.embed.add_author_footer(embed, inter.author)

        log_channel = self.bot.get_channel(config.log_channel)
        await log_channel.send(embed=embed)
