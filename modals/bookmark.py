import disnake

from buttons.bookmark import BookmarkView
from config.messages import Messages
from features.bookmark import BookmarkFeatures


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
                max_length=100,
            ),
        ]
        super().__init__(title="Bookmark", custom_id="bookmark_tag", timeout=300, components=components)

    async def callback(self, inter: disnake.ModalInteraction) -> None:
        inter.message = self.message
        title_name = Messages.bookmark_title(server=inter.guild.name)

        if not inter.text_values["name"] == "":
            title_name = inter.text_values["name"]
        embed, images, files_attached = await BookmarkFeatures.create_bookmark_embed(self, inter, title_name)

        try:
            if images:
                for image in images:
                    embed.append(await BookmarkFeatures.create_image_embed(self, inter, image, title_name))
            await inter.author.send(
                embeds=embed,
                view=BookmarkView(inter.message.jump_url),
                files=files_attached
                )
            await inter.response.send_message(
                Messages.bookmark_created(title_name=title_name),
                ephemeral=True
                )
        except disnake.HTTPException as e:
            if e.code == 50007:
                await inter.response.send_message(Messages.blocked_bot(user=inter.author.id),
                                                  ephemeral=True)
            else:
                raise e
