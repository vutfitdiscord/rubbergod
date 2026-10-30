import disnake

from buttons.base import BaseView
from config.app_config import config
from config.messages import Messages
from database.verification import ValidPersonDB
from features import verification
from rubbergod import Rubbergod
from utils.checks import PermissionsCheck

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
        await inter.response.defer()
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


class SchoolChangeView(BaseView):
    """Mod actions attached to the log of a school mismatch during verification."""

    def __init__(self, login: str, requested_school: str):
        super().__init__(timeout=None)
        self.add_item(
            disnake.ui.Button(
                label="Schválit změnu školy",
                style=disnake.ButtonStyle.success,
                custom_id=f"verify:school:approve:{requested_school}:{login}",
            )
        )
        self.add_item(
            disnake.ui.Button(
                label="Vymazat školu",
                style=disnake.ButtonStyle.danger,
                custom_id=f"verify:school:clear::{login}",
            )
        )


async def handle_school_change(inter: disnake.MessageInteraction) -> None:
    """Handle buttons of `SchoolChangeView` (persistent across restarts, state is in custom_id)."""
    _, _, action, school, login = inter.component.custom_id.split(":", 4)
    if not PermissionsCheck.is_mod_plus(inter, raise_exception=False):
        await inter.response.send_message(Messages.mod_plus_only, ephemeral=True)
        return

    service = verification.Verification(inter.bot)
    # only MUNI is stored explicitly, for VUT the school is refreshed from the VUT API on verify
    new_school = school if action == "approve" and school == "MUNI" else None
    if not service.reset_school(login, new_school):
        await inter.response.send_message(
            MessagesCZ.verify_school_change_missing(login=login), ephemeral=True
        )
        return

    if action == "approve":
        text = MessagesCZ.verify_school_change_approved(login=login, school=school)
    else:
        text = MessagesCZ.verify_school_change_cleared(login=login)
    embed = inter.message.embeds[0]
    embed.add_field(name="Vyřešeno", value=f"{inter.author.mention}: {text}", inline=False)
    await inter.response.edit_message(embed=embed, view=None)
