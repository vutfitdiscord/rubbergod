import disnake

from buttons.base import BaseView


class TrashView(BaseView):
    def __init__(self, custom_id: str = "trash:delete", row: int = None):
        super().__init__(timeout=None)
        self.add_item(disnake.ui.Button(
            emoji="🗑",
            style=disnake.ButtonStyle.danger,
            custom_id=custom_id,
            row=row
            ),
        )
