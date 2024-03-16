import disnake

from buttons.base import BaseView
from config.messages import Messages


class TrashView(BaseView):
    def __init__(self, custom_id: str = Messages.trash_delete_id, row: int = None):
        super().__init__(timeout=None)
        self.add_item(
            disnake.ui.Button(emoji="🗑", style=disnake.ButtonStyle.danger, custom_id=custom_id, row=row),
        )
