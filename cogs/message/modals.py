import disnake

from config.app_config import config
from utils.general import get_content_preview

from .features import create_message_log_embed
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
        self.old_content = message.content if message and edit else None  # Store old content for logging
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
        content_preview = get_content_preview(sent_message.content)
        attachments_count = len(self.files) if self.files else None

        embed = await create_message_log_embed(
            title="📤 Message sent",
            color=disnake.Color.blue(),
            channel=self.channel,
            message_link=sent_message.jump_url,
            content_preview=content_preview,
            attachments_count=attachments_count,
            author=inter.author,
        )

        log_channel = self.bot.get_channel(config.log_channel)
        await log_channel.send(embed=embed)

    async def _log_edit(self, inter: disnake.ModalInteraction) -> None:
        """Log message edit operation to log channel"""
        # self.message is guaranteed to be not None when this method is called
        if not self.message:
            return

        old_preview = get_content_preview(self.old_content)
        new_preview = get_content_preview(self.message.content)

        additional_fields = []
        if old_preview:
            additional_fields.append(("Old content preview", old_preview))

        embed = await create_message_log_embed(
            title="✏️ Message edited",
            color=disnake.Color.orange(),
            channel=self.message.channel,
            message_link=self.message.jump_url,
            content_preview=new_preview,
            author=inter.author,
            additional_fields=additional_fields if additional_fields else None,
        )

        log_channel = self.bot.get_channel(config.log_channel)
        await log_channel.send(embed=embed)
