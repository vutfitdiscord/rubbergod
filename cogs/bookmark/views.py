import disnake

from buttons.base import BaseView

from .messages_cz import MessagesCZ


class View(BaseView):
    def __init__(self, link: str):
        super().__init__(timeout=None)
        self.add_item(
            disnake.ui.Button(label=MessagesCZ.original_message, style=disnake.ButtonStyle.primary, url=link)
        )
        self.add_item(
            disnake.ui.Button(
                emoji="🗑", style=disnake.ButtonStyle.danger, custom_id=MessagesCZ.trash_delete_id
            )
        )
