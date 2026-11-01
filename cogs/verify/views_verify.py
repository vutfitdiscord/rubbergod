import disnake

from buttons.base import BaseView
from config.app_config import config
from config.messages import Messages
from database.verification import ValidPersonDB, VerifyStatus
from features import verification
from rubbergod import Rubbergod
from utils.checks import PermissionsCheck

from .messages_cz import MessagesCZ
from .modals_verify import VerifyModal


class VerifyView(BaseView):
    def __init__(self, login: str, mail_list: list[str], generation: int = 0):
        super().__init__(timeout=None)
        self.login = login
        if mail_list:
            self.add_item(MailDropdown(login, mail_list, generation=generation))

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
    def __init__(self, login: str, mail_list: list[str], generation: int = 0):
        super().__init__(login, mail_list, generation=generation)

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
    def __init__(self, login: str, mail_list: list[str], generation: int = 0):
        self.login = login
        self.mail_list = mail_list
        self.generation = generation
        super().__init__(
            placeholder=MessagesCZ.mail_alternative,
            min_values=1,
            max_values=1,
            custom_id=f"verify:mail:{login}:{generation}",
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
        user = ValidPersonDB.get_user_by_login(self.login)
        if not user or user.mail == inter.values[0]:
            return

        parts = (inter.component.custom_id or "").split(":")
        expected_gen = self.generation
        if len(parts) >= 4 and parts[0] == "verify" and parts[1] == "mail":
            try:
                expected_gen = int(parts[3])
            except ValueError:
                pass

        if (user.generation or 0) != expected_gen or user.year == "MUNI" or user.year is None:
            await inter.send(MessagesCZ.verify_view_outdated, ephemeral=True)
            return

        if user.status != VerifyStatus.InProcess.value:
            await inter.send(MessagesCZ.verify_view_outdated, ephemeral=True)
            return

        await self.log(inter.bot, user.mail, inter.values[0])
        user.set_mail(inter.values[0])
        # Resend code to new mail
        service = verification.Verification(inter.bot)
        await service.resend_code(self.login, inter)


class SchoolChangeView(BaseView):
    """Mod actions attached to the log of a school mismatch during verification."""

    def __init__(self, login: str, requested_school: str, generation: int, user_id: int):
        super().__init__(timeout=None)
        self.add_item(
            disnake.ui.Button(
                label="Schválit",
                style=disnake.ButtonStyle.success,
                custom_id=f"verify:school:approve:{requested_school}:{generation}:{user_id}:{login}",
            )
        )
        self.add_item(
            disnake.ui.Button(
                label="Zamítnout",
                style=disnake.ButtonStyle.danger,
                custom_id=f"verify:school:reject:{requested_school}:{generation}:{user_id}:{login}",
            )
        )


async def handle_school_change(inter: disnake.MessageInteraction) -> None:
    """Handle buttons of `SchoolChangeView` (persistent across restarts, state is in custom_id)."""
    if not PermissionsCheck.is_mod_plus(inter, raise_exception=False):
        await inter.response.send_message(Messages.mod_plus_only, ephemeral=True)
        return

    parts = inter.component.custom_id.split(":")
    # Legacy button format check (reject gracefully without crashing)
    if len(parts) < 7:
        login = parts[-1]
        await inter.response.send_message(MessagesCZ.verify_school_change_stale(login=login), ephemeral=True)
        return

    _, _, action, school, gen_str, user_id_str, login = parts

    user = ValidPersonDB.get_user_by_login(login)
    if user is None:
        await inter.response.send_message(
            MessagesCZ.verify_school_change_missing(login=login), ephemeral=True
        )
        return

    try:
        expected_generation = int(gen_str)
    except ValueError:
        expected_generation = -1

    if (user.generation or 0) != expected_generation:
        await inter.response.send_message(MessagesCZ.verify_school_change_stale(login=login), ephemeral=True)
        return

    await inter.response.defer()

    try:
        user_id = int(user_id_str)
    except ValueError:
        user_id = 0

    if action == "approve":
        service = verification.Verification(inter.bot)
        service.reset_school(login, None)
        text = MessagesCZ.verify_school_change_approved(login=login)

        if user_id:
            discord_user = inter.bot.get_user(user_id)
            if discord_user is None:
                try:
                    discord_user = await inter.bot.fetch_user(user_id)
                except disnake.HTTPException:
                    discord_user = None
            if discord_user is not None:
                try:
                    await discord_user.send(MessagesCZ.verify_school_change_user_cleared(login=login))
                except disnake.HTTPException:
                    pass
    else:
        # action == "reject"
        user.bump_generation()
        text = MessagesCZ.verify_school_change_rejected(login=login)

        if user_id:
            discord_user = inter.bot.get_user(user_id)
            if discord_user is None:
                try:
                    discord_user = await inter.bot.fetch_user(user_id)
                except disnake.HTTPException:
                    discord_user = None
            if discord_user is not None:
                try:
                    await discord_user.send(MessagesCZ.verify_school_change_user_rejected(login=login))
                except disnake.HTTPException:
                    pass

    embed = inter.message.embeds[0]
    embed.add_field(name="Vyřešeno", value=f"{inter.author.mention}: {text}", inline=False)
    await inter.edit_original_response(embed=embed, view=None)
