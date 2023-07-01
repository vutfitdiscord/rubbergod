import disnake

from database.verification import ValidPersonDB
from features import verification
from modals.verify import VerifyModal


class VerifyView(disnake.ui.View):
    def __init__(self, login: str):
        super().__init__(timeout=None)
        self.login = login

    @disnake.ui.button(
        label="Zadat kód",
        style=disnake.ButtonStyle.success,
        custom_id="verify:set_code",
    )
    async def code_success(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        user = ValidPersonDB.get_user_by_login(self.login)

        if user is None:
            raise Exception(f"Missing user {self.login} record in the database after sent mail.")

        await inter.response.send_modal(VerifyModal(user.login))


class VerifyWithResendButtonView(VerifyView):
    def __init__(self, login: str):
        super().__init__(login)

    @disnake.ui.button(
        label="Znovu odeslat kód",
        style=disnake.ButtonStyle.danger,
        custom_id="verify:missing_code",
    )
    async def missing_code(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        service = verification.Verification(inter.bot)
        await service.resend_code(self.login, inter)
