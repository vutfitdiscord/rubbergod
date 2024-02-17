import disnake
from disnake.ext import commands

from buttons.general import TrashView
from config.messages import Messages
from database.contestvote import ContestVoteDB
from features.contestvote import get_contribution_id


class DenyContributionModal(disnake.ui.Modal):
    def __init__(self, bot: commands.Bot, inter: disnake.MessageInteraction) -> None:
        self.bot = bot
        self.inter = inter
        self.contribution_id = get_contribution_id(inter.message.content)
        self.title = Messages.contest_modal_title(id=self.contribution_id)
        components = [
            disnake.ui.TextInput(
                label=self.title,
                placeholder=Messages.contest_modal_placeholder,
                custom_id='contest:reason',
                style=disnake.TextInputStyle.long,
                required=False,
                max_length=1900,
            )
        ]

        super().__init__(
            title=self.title,
            custom_id='contest_vote_modal',
            timeout=900,
            components=components
        )

    async def callback(self, inter: disnake.ModalInteraction) -> None:
        contribution_author_id = ContestVoteDB.get_contribution_author(self.contribution_id)
        author = await self.bot.get_or_fetch_user(contribution_author_id)

        trash = TrashView()
        file = await inter.message.attachments[0].to_file()
        reason = inter.text_values['contest:reason'].strip()

        if reason:
            message = Messages.contest_contribution_denied(
                id=self.contribution_id,
                reason=reason,
                author=inter.author.display_name
            )
            await author.send(inter.message.content, file=file, view=trash)
            await author.send(message, view=trash)
        else:
            message = Messages.contest_successful_deletion_no_reason(author=inter.author.display_name)

        await inter.send(message)
        await inter.message.edit(view=None)
        await inter.message.unpin()
