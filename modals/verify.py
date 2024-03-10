import disnake

from config.messages import Messages
from features import verification


class VerifyModal(disnake.ui.Modal):
    def __init__(self, login: str) -> None:
        self.login = login

        components = [
            disnake.ui.TextInput(
                label="Ověřovací kód",
                placeholder="Ověřovací kód",
                custom_id="code",
                style=disnake.TextInputStyle.short,
                required=True,
                min_length=6,
                max_length=10,
            )
        ]
        super().__init__(
            title=Messages.verify_subject, components=components, custom_id="verify_modal", timeout=600
        )

    async def callback(self, inter: disnake.ModalInteraction) -> None:
        code = inter.text_values["code"].strip().upper()
        service = verification.Verification(inter.bot)
        await service.finish_verify(inter, code, self.login)
