import disnake
from buttons.base import BaseView


class ModerationView(BaseView):
    def __init__(self, link, label, style):
        super().__init__(timeout=None)
        self.add_item(disnake.ui.Button(
            label=label,
            style=style,
            custom_id="moderation:resolve")
        )
        self.add_item(disnake.ui.Button(
            label="Original message",
            style=disnake.ButtonStyle.primary,
            url=link)
        )
