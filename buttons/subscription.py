import disnake

from buttons.base import BaseView


class SubscriptionView(BaseView):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(disnake.ui.Button(
            emoji="🗑",
            style=disnake.ButtonStyle.danger,
            custom_id="subscription:delete")
        )
