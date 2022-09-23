import disnake

from buttons.base import BaseView


class IconView(BaseView):

    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(disnake.ui.Button(
            emoji="🗑",
            style=disnake.ButtonStyle.danger,
            custom_id="icon:delete",
            row=1),
        )
