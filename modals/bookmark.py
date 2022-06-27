import disnake
from buttons.bookmark import BookmarkView
from config.messages import Messages


class BookmarkModal(disnake.ui.Modal):
    def __init__(self, message) -> None:
        self.message = message
        components = [
            disnake.ui.TextInput(
                label="Bookmark name",
                placeholder="Bookmark name",
                custom_id="name",
                style=disnake.TextInputStyle.short,
                required=False,
                max_length=50,
            ),
        ]
        super().__init__(title="Bookmark", custom_id="bookmark_tag", timeout=300, components=components)

    async def callback(self, inter: disnake.ModalInteraction) -> None:
        view = BookmarkView()
        if inter.text_values["name"] == "":
            bookmark_name = Messages.bookmark_title
        else:
            bookmark_name = inter.text_values["name"]

        if self.message.embeds:
            for embed in self.message.embeds:
                content = embed.to_dict()
        else:
            content = self.message.content

        embed = disnake.Embed(title=bookmark_name, colour=self.message.author.colour)
        embed.set_author(name=self.message.author, icon_url=self.message.author.avatar)
        embed.add_field(name="Zpráva", value=content, inline=False)
        embed.add_field(
            name="Channel",
            value=f"[Jump to original message]({self.message.jump_url}) in {self.message.channel.mention}"
        )

        await inter.author.send(embed=embed, view=view)
        await inter.response.send_message(f"Záložka **{bookmark_name}** vytvořena", ephemeral=True)
