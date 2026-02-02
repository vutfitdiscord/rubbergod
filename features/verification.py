import random
import re
import smtplib
import ssl
import string
from datetime import datetime
from email.mime.text import MIMEText

import disnake

from cogs.verify.messages_cz import MessagesCZ
from cogs.verify.views_verify import VerifyView, VerifyWithResendButtonView
from config.app_config import config
from database.verification import ValidPersonDB, VerifyStatus
from features.base_feature import BaseFeature
from features.verify_helper import VerifyHelper
from rubbergod import Rubbergod

MIT_SPECIALIZATIONS = [
    "MBS", "MBI", "MIS", "MIN", "MMI", "MMM", "MGM", "MGMe",
    "MPV", "MSK", "NADE", "NBIO", "NGRI", "NNET", "NVIZ", "NCPS",
    "NSEC", "NEMB", "NHPC", "NISD", "NIDE", "NISY", "NMAL", "NMAT", "NSEN",
    "NVER", "NSPE", "MGH", "MITP-EN",
]  # fmt: skip

FACULTY_NAMES = ["FA", "FAST", "FAVU", "FCH", "FEKT", "FP", "FSI", "ÚSI",]  # fmt: skip


class Verification(BaseFeature):
    def __init__(self, bot: Rubbergod):
        super().__init__(bot)
        self.helper = VerifyHelper(bot)

    def send_mail(self, receiver_email: str, contents: str, subject: str = "") -> None:
        msg = MIMEText(contents, "plain", "utf-8")
        msg["Subject"] = subject
        msg["To"] = receiver_email
        msg["Date"] = datetime.now().isoformat()
        msg["From"] = config.email_addr

        with smtplib.SMTP_SSL(
            config.email_smtp_server,
            config.email_smtp_port,
            context=ssl.create_default_context(),
        ) as server:
            server.login(config.email_name, config.email_pass)
            server.sendmail(config.email_addr, receiver_email, msg.as_string())

    def send_mail_verified(self, receiver_email: str, user: str):
        """Send mail with instructions in case of blocked DMs"""
        self.send_mail(
            receiver_email,
            MessagesCZ.verify_post_verify_info_mail,
            f"{user} {MessagesCZ.verify_verify_success_mail}",
        )

    async def gen_code_and_send_mail(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: ValidPersonDB,
        mail_postfix: str,
        is_resend: bool = False,
        dry_run: bool = False,
    ):
        mail_address = user.get_mail(mail_postfix)

        if not dry_run:
            # Generate a verification code
            code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
            mail_content = MessagesCZ.verify_mail_content(code=code)
            # Save the newly generated code into the database
            user.save_sent_code(code)
            self.send_mail(mail_address, mail_content, MessagesCZ.verify_subject)

        mail_list = await self.helper.get_mails(user.login)
        if not is_resend:
            success_message = MessagesCZ.verify_send_success(
                user=inter.user.id,
                mail=mail_address,
                subject=MessagesCZ.verify_subject,
            )
            view = VerifyWithResendButtonView(user.login, mail_list)
            await inter.edit_original_response(content=success_message, view=view)
        else:
            success_message = MessagesCZ.verify_resend_success(
                user=inter.user.id,
                mail=mail_address,
                subject=MessagesCZ.verify_subject,
            )
            view = VerifyView(user.login, mail_list)
            await inter.edit_original_response(content=success_message, view=view)

    async def send_code_muni(self, login: str, inter: disnake.ApplicationCommandInteraction) -> bool:
        try:
            int(login)
        except ValueError:
            msg = MessagesCZ.invalid_login(user=inter.user.id, admin=config.admin_ids[0])
            await inter.edit_original_response(msg)
            await self.log_verify_fail(inter, "getcode (MUNI)", str({"login": login}))
            return False

        user = ValidPersonDB.get_user_by_login(login)

        if user is not None and user.status != VerifyStatus.Unverified.value:
            if user.status == VerifyStatus.InProcess.value:
                await self.gen_code_and_send_mail(inter, user, "mail.muni.cz", dry_run=True)
                return True
            msg = MessagesCZ.verify_step_done(
                user=inter.user.id,
                admin=config.admin_ids[0],
            )
            await inter.send(content=msg)
            await self.log_verify_fail(
                inter,
                "getcode (MUNI) - Invalid verify state",
                str(user.__dict__),
            )
            return False

        user = ValidPersonDB.get_user_with_status(login, status=VerifyStatus.Unverified.value)
        if user is None:
            user = ValidPersonDB.add_user(login, "MUNI", status=VerifyStatus.Unverified.value)
        await self.gen_code_and_send_mail(inter, user, "mail.muni.cz")
        return True

    async def send_code_vut(self, login: str, inter: disnake.ApplicationCommandInteraction) -> bool:
        user = await self.helper.check_api(login)
        if user is None:
            await inter.send(MessagesCZ.invalid_login(user=inter.author.id, admin=config.admin_ids[0]))
            return False

        if user.status == VerifyStatus.Unverified.value:
            await self.gen_code_and_send_mail(inter, user, "stud.fit.vutbr.cz")
            return True

        if user.status == VerifyStatus.InProcess.value:
            await self.gen_code_and_send_mail(inter, user, "stud.fit.vutbr.cz", dry_run=True)
            return True

        msg = MessagesCZ.verify_step_done(
            user=inter.user.id,
            admin=config.admin_ids[0],
        )
        await inter.edit_original_response(content=msg)
        await self.log_verify_fail(
            inter,
            "getcode (xlogin) - Invalid verify state",
            str(user.__dict__),
        )
        return False

    async def send_code(
        self, login: str, inter: disnake.ApplicationCommandInteraction, muni: bool = False
    ) -> bool:
        # return True if code was successfully sent
        # Check if the user doesn't have the verify role
        if not await self.helper.has_role(inter.user, config.verification_role) or await self.helper.has_role(
            inter.user, "Host"
        ):
            # Some of them will use 'xlogin00' as stated in help, cuz they dumb
            if login == "xlogin00":
                await self.send_xlogin_info(inter)
                return False
            if muni:
                return await self.send_code_muni(login, inter)
            else:
                return await self.send_code_vut(login, inter)
        else:
            msg = MessagesCZ.verify_already_verified(user=inter.user.id, admin=config.admin_ids[0])
            await inter.send(content=msg)

        return False

    async def resend_code(self, login: str, inter: disnake.ApplicationCommandInteraction) -> None:
        if await self.helper.has_role(inter.user, config.verification_role):
            return  # User is now verified.

        user = ValidPersonDB.get_user_by_login(login)
        if user is None:
            raise Exception(
                "The user requested to resend the verification code, but it does not exist in the DB."
            )

        mail_postfix = self.get_mail_postfix(login)
        await self.gen_code_and_send_mail(inter, user, mail_postfix, True)

    @staticmethod
    def transform_year(raw_year: str):
        """Parses year string originally from /etc/passwd into a role name"""

        if raw_year.lower() == "exstudent":
            return "ExStudent"

        year_parts = list(filter(lambda x: len(x.strip()) > 0, raw_year.split()))

        if year_parts[0] == "FIT":  # FIT student, or some VUT student.
            if len(year_parts) != 3:
                # ['FIT'], ['FIT', '1r'], .... Who knows. Other faculty students, ExStudents, ...
                return None

            year_value_match = re.search(r"(\d*)r?", year_parts[2])
            if year_value_match is None:
                return None
            year_value = int(year_value_match.group(1))

            if year_parts[1] in ["BIT", "BITP"]:
                return "3BIT+" if year_value >= 3 else f"{year_value}BIT"
            elif year_parts[1] in ["BCH", "CZV"]:
                return "1BIT"  # TODO: fix erasmus students (BCH)
            elif year_parts[1] in MIT_SPECIALIZATIONS:
                return "2MIT+" if year_value >= 2 else f"{year_value}MIT"
            elif year_parts[1] in ["DVI4", "DRH", "DITP", "DITP-EN"]:
                return "Doktorand"
        elif year_parts[0] in ["employee", "external employee"]:
            return "Vyucujici/Zamestnanec"
        elif year_parts[0] in FACULTY_NAMES:
            # Other VUT faculties
            return "VUT"
        elif len(year_parts) == 1 and year_parts[0] == "MUNI":  # Maybe MUNI?
            return "MUNI"

        return None

    @staticmethod
    def get_mail_postfix(login: str):
        return "mail.muni.cz" if login[0] != "x" and login.isnumeric() else "stud.fit.vutbr.cz"

    async def finish_verify(self, inter: disnake.ModalInteraction, code: str, login: str) -> None:
        new_user = ValidPersonDB.get_user_by_login(login)
        if new_user is not None:
            if code != new_user.code:
                await inter.response.send_message(MessagesCZ.verify_verify_wrong_code)
                await self.log_verify_fail(
                    inter,
                    "Verify (with code) - Wrong code",
                    str({"login": login, "code(Input)": code, "code(DB)": new_user.code}),
                )
                return

            # Try and transform the year into the role name
            year = self.transform_year(new_user.year)

            if year is None:
                msg = MessagesCZ.verify_verify_manual(
                    user=inter.user.id,
                    admin=config.admin_ids[0],
                    year=str(new_user.year),
                )
                await inter.response.send_message(msg)
                await self.log_verify_fail(
                    inter, "Verify (with code) (Invalid year)", str({"login": login, "year": new_user.year})
                )
                return

            try:
                # Get server verify role
                verify = disnake.utils.get(inter.guild.roles, name=config.verification_role)
                year = disnake.utils.get(inter.guild.roles, name=year)
                member = inter.user
            except AttributeError:
                # DMs
                guild = self.bot.get_guild(config.guild_id)
                verify = disnake.utils.get(guild.roles, name=config.verification_role)
                year = disnake.utils.get(guild.roles, name=year)
                member = guild.get_member(inter.user.id)

            await self.clear_host_roles(inter)

            await member.add_roles(verify)
            await member.add_roles(year)

            try:
                new_user.save_verified(inter.user.id)
            except Exception:
                return await self.log_verify_fail(
                    inter,
                    "Verify (with code) (User already verified?)",
                    str({"login": login, "year": new_user.year}),
                )

            verify_success_msg = MessagesCZ.verify_verify_success(user=inter.user.id)
            try:
                await member.send(verify_success_msg)
                await member.send(MessagesCZ.verify_post_verify_info, suppress_embeds=True)
            except disnake.errors.Forbidden:
                mail = new_user.get_mail(self.get_mail_postfix(login))
                self.send_mail_verified(mail, member)
            await inter.response.send_message(verify_success_msg)
        else:
            msg = MessagesCZ.verify_verify_not_found(user=inter.user.id, admin=config.admin_ids[0])
            await inter.response.send_message(msg)
            await self.log_verify_fail(
                inter, "Verify (with code) - Not exists in DB", str({"login": login, "code": code})
            )

    async def log_verify_fail(self, inter: disnake.ApplicationCommand, phase: str, data: str):
        embed = disnake.Embed(title="Neúspěšný pokus o verify", color=disnake.Colour.yellow())
        embed.add_field(name="User", value=inter.author.mention)
        embed.add_field(name="Verify phase", value=phase)
        embed.add_field(name="Data", value=data, inline=False)
        await self.bot.get_channel(config.log_channel).send(embed=embed)

    async def send_xlogin_info(self, inter: disnake.ApplicationCommandInteraction):
        guild = self.bot.get_guild(config.guild_id)
        fp = await guild.fetch_emoji(585915845146968093)
        await inter.edit_original_response(
            content=MessagesCZ.verify_send_dumbshit(user=inter.user.id, emote=str(fp))
        )

    async def clear_host_roles(self, inter: disnake.ApplicationCommandInteraction | disnake.ModalInteraction):
        """Removes host roles (Host, Zajemce o studium, Verify)"""
        guild = self.bot.get_guild(config.guild_id)
        member = inter.user if isinstance(inter.user, disnake.Member) else guild.get_member(inter.user.id)

        newbie = disnake.utils.get(guild.roles, id=config.newbie_role)
        host = disnake.utils.get(guild.roles, name="Host")
        verify = disnake.utils.get(guild.roles, name="Verify")
        zajemce = disnake.utils.get(guild.roles, name="ZajemceoStudium")
        await member.remove_roles(host, newbie, verify, zajemce, reason="Verify user")
