import disnake


class BookmarkView(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @disnake.ui.button(label="Delete bookmark", style=disnake.ButtonStyle.danger, custom_id="bookmark:delete")
    async def delete_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        pass
