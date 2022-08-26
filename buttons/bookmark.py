import disnake


class BookmarkView(disnake.ui.View):
    def __init__(self, link):
        super().__init__(timeout=None)
        self.add_item(disnake.ui.Button(
            label="Původní zpráva",
            style=disnake.ButtonStyle.primary,
            url=link)
            )
        self.add_item(disnake.ui.Button(
            emoji="🗑",
            label="Smazat záložku",
            style=disnake.ButtonStyle.danger,
            custom_id="bookmark:delete")
            )
