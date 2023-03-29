import disnake

from buttons.base import BaseView


class ModerationView(BaseView):
    def __init__(self, label, custom_id):
        super().__init__(timeout=None)
        self.add_item(disnake.ui.Button(
            label=label,
            style=disnake.ButtonStyle.gray,
            custom_id=custom_id)
        )
