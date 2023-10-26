import disnake

from buttons.base import BaseView


class ErrorView(BaseView):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(disnake.ui.Button(
            emoji="📄",
            label="Traceback",
            style=disnake.ButtonStyle.danger,
            custom_id="error:traceback")
        )
