from io import BytesIO

import disnake

from buttons.base import BaseView
from database.stats import ErrorEvent

from .general import TrashView


class ErrorView(BaseView):
    def __init__(self):
        super().__init__(timeout=None)

    async def create_traceback_file(self, inter: disnake.MessageInteraction) -> disnake.File | None:
        if not inter.message.embeds:
            return None
        footer_text = inter.message.embeds[0].footer.text
        if not footer_text or ":" not in footer_text:
            return None
        raw_id = footer_text.split(":")[-1].strip()
        try:
            error_id = int(raw_id)
        except ValueError:
            return None

        event = ErrorEvent.get_traceback(error_id)
        if not event or not event.traceback:
            return None
        with BytesIO(bytes(event.traceback, "utf-8")) as file_binary:
            file = disnake.File(fp=file_binary, filename="traceback.txt")
        return file

    @disnake.ui.button(
        emoji="📄", label="Traceback", style=disnake.ButtonStyle.danger, custom_id="error:traceback"
    )
    async def traceback(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        await inter.response.defer()
        file = await self.create_traceback_file(inter)
        if not file:
            await inter.message.delete()
            return

        await inter.send(file=file, ephemeral=True)

    @disnake.ui.button(
        emoji="📄", label="Traceback DM", style=disnake.ButtonStyle.danger, custom_id="error:traceback_dm"
    )
    async def traceback_dm(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        await inter.response.defer()
        file = await self.create_traceback_file(inter)
        if not file:
            await inter.message.delete()
            return

        await inter.author.send(file=file, view=TrashView())
