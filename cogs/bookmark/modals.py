import disnake

from .features import Features
from .messages_cz import MessagesCZ
from .views import BookmarkView


class Modal(disnake.ui.Modal):
    def __init__(self, message) -> None:
        self.message = message
        components = [
            disnake.ui.TextInput(
                label="Bookmark name",
                placeholder="Bookmark name",
                custom_id="name",
                style=disnake.TextInputStyle.short,
                required=False,
                max_length=100,
            ),
        ]
        super().__init__(title="Bookmark", custom_id="bookmark_tag", timeout=300, components=components)

    async def callback(self, inter: disnake.ModalInteraction) -> None:
        inter.message = self.message
        title_name = MessagesCZ.bookmark_title(server=inter.guild.name)

        if not inter.text_values["name"] == "":
            title_name = inter.text_values["name"]
        embed, images, files_attached = await Features.create_bookmark_embed(self, inter, title_name)

        try:
            if images:
                for image in images:
                    embed.append(await Features.create_image_embed(self, inter, image, title_name))
            await inter.author.send(
                embeds=embed, view=BookmarkView(inter.message.jump_url), files=files_attached
            )
            await inter.response.send_message(
                MessagesCZ.bookmark_created(title_name=title_name), ephemeral=True
            )
        except disnake.HTTPException as e:
            if e.code == 50007:
                await inter.response.send_message(
                    MessagesCZ.blocked_bot(user=inter.author.id), ephemeral=True
                )
            else:
                raise e
