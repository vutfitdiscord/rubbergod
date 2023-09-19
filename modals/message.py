import disnake

from config.messages import Messages


class MessageModal(disnake.ui.Modal):
    def __init__(
        self,
        bot,
        title: str,
        channel: disnake.TextChannel = None,
        message: disnake.Message = None,
        edit: bool = False
    ) -> None:
        self.bot = bot
        self.title = title
        self.channel = channel
        self.message = message
        self.edit = edit
        components = [
            disnake.ui.TextInput(
                label="Message content",
                custom_id="content",
                style=disnake.TextInputStyle.long,
                required=True,
                value=self.message.content if edit else None,
                max_length=2000,
            )
        ]

        super().__init__(
            title=self.title,
            custom_id="message_modal",
            timeout=900,
            components=components
        )

    async def callback(self, inter: disnake.ModalInteraction) -> None:
        if self.edit:
            await self.message.edit(inter.text_values["content"])
            await inter.send(Messages.message_sent(channel=self.message.channel.mention), ephemeral=True)
            return

        await self.channel.send(inter.text_values["content"])
        await inter.send(Messages.message_sent(channel=self.channel.mention), ephemeral=True)
