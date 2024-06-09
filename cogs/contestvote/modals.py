import disnake

from buttons.general import TrashView
from database.contestvote import ContestVoteDB
from rubbergod import Rubbergod

from . import features
from .messages_cz import MessagesCZ


class DenyContributionModal(disnake.ui.Modal):
    def __init__(self, bot: Rubbergod, inter: disnake.MessageInteraction) -> None:
        self.bot = bot
        self.inter = inter
        self.contribution_id = features.get_contribution_id(inter.message.content)
        self.title = MessagesCZ.modal_title(id=self.contribution_id)
        components = [
            disnake.ui.TextInput(
                label=self.title,
                placeholder=MessagesCZ.modal_placeholder,
                custom_id="contest:reason",
                style=disnake.TextInputStyle.long,
                required=False,
                max_length=1900,
            )
        ]

        super().__init__(title=self.title, custom_id="contest_vote_modal", timeout=900, components=components)

    async def callback(self, inter: disnake.ModalInteraction) -> None:
        contribution_author_id = ContestVoteDB.get_contribution_author(self.contribution_id)
        author = await self.bot.get_or_fetch_user(contribution_author_id)

        trash = TrashView()
        file = await inter.message.attachments[0].to_file()
        reason = inter.text_values["contest:reason"].strip()

        if reason:
            message = MessagesCZ.contribution_denied(
                id=self.contribution_id, reason=reason, author=inter.author.display_name
            )
            await author.send(inter.message.content, file=file, view=trash)
            await author.send(message, view=trash)
        else:
            message = MessagesCZ.successful_deletion_no_reason(author=inter.author.display_name)

        await inter.send(message)
        await inter.message.edit(view=None)
        await inter.message.unpin()
