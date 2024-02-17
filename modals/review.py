import disnake

from config.messages import Messages
from features.review import ReviewManager


class ReviewModal(disnake.ui.Modal):
    def __init__(self, bot) -> None:
        self.manager = ReviewManager(bot=bot)
        components = [
            disnake.ui.TextInput(custom_id='review_subject', label=Messages.review_subject_label),
            disnake.ui.Select(
                custom_id='review_anonym',
                options=[
                    disnake.SelectOption(label=Messages.review_anonym_label, value=True, default=True),
                    disnake.SelectOption(label=Messages.review_signed_label, value=False),
                ],
            ),
            disnake.ui.Select(
                custom_id='review_tier',
                placeholder=Messages.review_tier_placeholder,
                options=[
                    disnake.SelectOption(label='A', value=0, description=Messages.review_tier_0_desc),
                    disnake.SelectOption(label='B', value=1, description=Messages.review_tier_1_desc),
                    disnake.SelectOption(label='C', value=2, description=Messages.review_tier_2_desc),
                    disnake.SelectOption(label='D', value=3, description=Messages.review_tier_3_desc),
                    disnake.SelectOption(label='E', value=4, description=Messages.review_tier_4_desc),
                ],
            ),
            disnake.ui.TextInput(
                custom_id='review_text',
                label=Messages.review_text_label,
                style=disnake.TextInputStyle.paragraph,
                required=False,
            ),
        ]
        super().__init__(
            title=Messages.review_modal_title,
            components=components,
            custom_id='review_modal',
        )

    async def callback(self, interaction: disnake.ModalInteraction) -> None:
        result = self.manager.add_review(
            interaction.author,
            interaction.text_values['review_subject'].lower(),
            interaction.select_values['review_tier'][0],
            interaction.select_values['review_anonym'][0],
            interaction.text_values['review_text'],
        )
        if not result:
            await interaction.send(Messages.review_wrong_subject, ephemeral=True)
        else:
            await interaction.send(Messages.review_added)
