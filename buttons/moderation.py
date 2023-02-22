import disnake
from buttons.base import BaseView


class ModerationView(BaseView):
    def __init__(self, link, embed):
        super().__init__(timeout=None)
        self.embed = embed
        self.add_item(disnake.ui.Button(
            label="Original message",
            style=disnake.ButtonStyle.primary,
            url=link)
        )

    @disnake.ui.button(label="Unresolved", style=disnake.ButtonStyle.gray)
    async def solve_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        if button.label == "Unresolved":
            button.label = "Resolved"
            button.style = disnake.ButtonStyle.green
            for field in self.embed["fields"]:
                if field["name"] == "Resolved by:":
                    field["value"] = inter.author.mention
        else:
            button.label = "Unresolved"
            button.style = disnake.ButtonStyle.gray
            for field in self.embed["fields"]:
                if field["name"] == "Resolved by:":
                    field["value"] = "---"

        await inter.response.edit_message(embed=disnake.Embed.from_dict(self.embed), view=self)
