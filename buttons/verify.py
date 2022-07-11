import disnake
from features import verification, dynamic_verify
from modals.verify import VerifyModal
from config.app_config import config
from config.messages import Messages


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
        service = verification.Verification(inter.bot)
        user = service.repo.get_user_by_login(self.login)

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


class DynamicVerifyRequestView(disnake.ui.View):
    def __init__(self, rule_id: str, user_id: int):
        self.rule_id = rule_id
        self.user_id = user_id
        super().__init__(timeout=None)

    @disnake.ui.button(label="Schválit", style=disnake.ButtonStyle.success, custom_id="dynamic_verify:accept")
    async def accept_access(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        service = dynamic_verify.DynamicVerifyManager(inter.bot)
        await service.apply_rule(self.rule_id, self.user_id, inter)

    @disnake.ui.button(
        label="Zamítnout", style=disnake.ButtonStyle.danger, custom_id="dynamic_verify:decline"
    )
    async def decline_access(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.message.delete()

        guild = inter.guild if inter.guild is not None else inter.bot.get_guild(config.guild_id)
        member = await guild.get_or_fetch_member(self.user_id)
        if member is not None:
            try:
                await member.send(Messages.dynamic_verify_declined)
            except disnake.HTTPException:
                pass
