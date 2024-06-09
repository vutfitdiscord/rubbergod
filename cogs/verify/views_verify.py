import disnake

from buttons.base import BaseView
from config.app_config import config
from database.verification import ValidPersonDB
from features import verification
from rubbergod import Rubbergod

from .messages_cz import MessagesCZ
from .modals_verify import VerifyModal


class VerifyView(BaseView):
    def __init__(self, login: str, mail_list: list[str]):
        super().__init__(timeout=None)
        self.login = login
        if mail_list:
            self.add_item(MailDropdown(login, mail_list))

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
    def __init__(self, login: str, mail_list: list[str]):
        super().__init__(login, mail_list)

    @disnake.ui.button(
        label="Znovu odeslat kód",
        style=disnake.ButtonStyle.danger,
        custom_id="verify:missing_code",
    )
    async def missing_code(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        service = verification.Verification(inter.bot)
        await service.resend_code(self.login, inter)


class MailDropdown(disnake.ui.StringSelect):
    def __init__(self, login: str, mail_list: list[str]):
        self.login = login
        self.mail_list = mail_list
        super().__init__(
            placeholder=MessagesCZ.mail_alternative,
            min_values=1,
            max_values=1,
            options=self.create_select(),
        )

    def create_select(self) -> list[disnake.SelectOption]:
        """Create select options from mail list."""
        options = []
        for mail in self.mail_list:
            options.append(disnake.SelectOption(label=mail, value=mail))
        return options

    async def log(self, bot: Rubbergod, old_mail: str, new_mail: str) -> None:
        log_channel = bot.get_channel(config.log_channel)
        embed = disnake.Embed(
            title=MessagesCZ.mail_changed,
            description=MessagesCZ.mail_changed_desc(login=self.login, old=old_mail, new=new_mail),
            color=disnake.Color.yellow(),
        )
        await log_channel.send(embed=embed)

    async def callback(self, inter: disnake.MessageInteraction) -> None:
        await inter.response.defer()
        # Set new mail to DB
        user = ValidPersonDB.get_user_by_login(self.login)
        if not user or user.mail == inter.values[0]:
            return
        await self.log(inter.bot, user.mail, inter.values[0])
        user.set_mail(inter.values[0])
        # Resend code to new mail
        service = verification.Verification(inter.bot)
        await service.resend_code(self.login, inter)
