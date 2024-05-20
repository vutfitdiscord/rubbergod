import disnake

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
                required=True,
                value=message.content if message and edit else None,
                max_length=2000,
            )
        ]

        super().__init__(title=self.title, custom_id="message_modal", timeout=900, components=components)

    async def callback(self, inter: disnake.ModalInteraction) -> None:
        if self.edit and self.message:
            await self.message.edit(inter.text_values["content"])
            await inter.send(MessagesCZ.message_sent(channel=self.message.channel.mention), ephemeral=True)
            return

        if self.channel:
            await self.channel.send(inter.text_values["content"], files=self.files)
            await inter.send(MessagesCZ.message_sent(channel=self.channel.mention), ephemeral=True)
