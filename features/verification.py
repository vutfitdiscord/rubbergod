import random
import smtplib
import ssl
import string
import re

import disnake
from disnake import Member
from disnake.ext.commands import Bot

import utils
from config.app_config import config
from config.messages import Messages
from features.base_feature import BaseFeature
from repository.user_repo import UserRepository, VerifyStatus
from repository.database.verification import Valid_person
from email.mime.text import MIMEText
from buttons.verify import VerifyWithResendButtonView, VerifyView
from datetime import datetime


class Verification(BaseFeature):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.repo = UserRepository()

    def send_mail(self, receiver_email: str, contents: str, subject: str = "") -> None:
        msg = MIMEText(contents)
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
            Messages.verify_post_verify_info_mail,
            f"{user} {Messages.verify_verify_success_mail}",
        )

    async def has_role(self, user, role_name: str) -> bool:
        if type(user) == Member:
            return utils.has_role(user, role_name)
        else:
            guild = await self.bot.fetch_guild(config.guild_id)
            member = await guild.fetch_member(user.id)
            return utils.has_role(member, role_name)

    async def gen_code_and_send_mail(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: Valid_person,
        mail_postfix: str,
        is_resend: bool = False,
    ):
        # Generate a verification code
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=20))
        msg = f"{config.default_prefix}verify {user.login} {code}"

        mail_address = user.get_mail(mail_postfix)
        self.send_mail(mail_address, msg, Messages.verify_subject)

        # Save the newly generated code into the database
        self.repo.save_sent_code(user.login, code)

        success_message = utils.fill_message(
            "verify_resend_success" if is_resend else "verify_send_success",
            user=inter.user.id,
            mail=mail_address,
            subject=Messages.verify_subject,
        )

        if not is_resend:
            await inter.send(content=success_message, view=VerifyWithResendButtonView(user.login), ephemeral=True)
        else:
            await inter.response.edit_message(content=success_message, view=VerifyView(user.login))

    async def send_code(
        self, login: str, inter: disnake.ApplicationCommandInteraction
    ) -> None:
        # Check if the user doesn't have the verify role
        if not await self.has_role(inter.user, config.verification_role):
            # Some of them will use 'xlogin00' as stated in help, cuz they dumb
            if login == "xlogin00":
                await self.send_xlogin_info(inter)
                return

            if login[0] == "x":
                # VUT
                # Check if the login we got is in the database
                user = self.repo.get_user_by_login(login)

                if user is None:
                    msg = utils.fill_message(
                        "verify_unknown_login",
                        user=inter.user.id,
                        admin=config.admin_ids[0],
                    )
                    await inter.user.send(content=msg)
                    await self.log_verify_fail(
                        inter, "getcode (xlogin) - Unknown login", str({"login": login})
                    )
                elif user is not None and user.status != VerifyStatus.Unverified.value:
                    msg = utils.fill_message(
                        "verify_step_done",
                        user=inter.user.id,
                        admin=config.admin_ids[0],
                    )
                    await inter.send(content=msg)
                    await self.log_verify_fail(
                        inter,
                        "getcode (xlogin) - Invalid verify state",
                        str(user.__dict__),
                    )
                else:
                    await self.gen_code_and_send_mail(inter, user, "stud.fit.vutbr.cz")
            else:
                # MUNI
                try:
                    int(login)
                except ValueError:
                    msg = utils.fill_message(
                        "invalid_login",
                        user=inter.user.id,
                        admin=config.admin_ids[0],
                    )
                    await inter.send(msg)
                    await self.log_verify_fail(
                        inter, "getcode (MUNI)", str({"login": login})
                    )

                user = self.repo.get_user_by_login(login)

                if user is not None and user.status != VerifyStatus.Unverified.value:
                    msg = utils.fill_message(
                        "verify_step_done",
                        user=inter.user.id,
                        admin=config.admin_ids[0],
                    )
                    await inter.send(conetnt=msg)
                    await self.log_verify_fail(
                        inter,
                        "getcode (MUNI) - Invalid verify state",
                        str(user.__dict__),
                    )
                    return

                user = self.repo.get_user(login, status=VerifyStatus.Unverified.value)
                if user is None:
                    user = self.repo.add_user(
                        login, "MUNI", status=VerifyStatus.Unverified.value
                    )
                await self.gen_code_and_send_mail(inter, user, "mail.muni.cz")
        else:
            msg = utils.fill_message(
                "verify_already_verified", user=inter.user.id, admin=config.admin_ids[0]
            )
            await inter.send(content=msg)

    async def resend_code(
        self, login: str, inter: disnake.ApplicationCommandInteraction
    ) -> None:
        if await self.has_role(inter.user, config.verification_role):
            return  # User is now verified.

        user = self.repo.get_user_by_login(login)
        if user is None:
            raise Exception(
                "The user requested to resend the verification code, but it does not exist in the DB."
            )

        mail_postfix = (
            "mail.muni.cz"
            if login[0] != "x" and login.isnumeric()
            else "stud.fit.vutbr.cz"
        )
        await self.gen_code_and_send_mail(inter, user, mail_postfix, True)

    @staticmethod
    def transform_year(raw_year: str):
        """Parses year string originally from /etc/passwd into a role name"""

        if raw_year.lower() == "dropout":
            return "Dropout"

        year_parts = list(filter(lambda x: len(x.strip()) > 0, raw_year.split()))

        if year_parts[0] == "FIT":  # FIT student, or some VUT student.
            if len(year_parts) != 3:
                # ['FIT'], ['FIT', '1r'], .... Who knows. Other faculty students, dropouts, ...
                return None

            year_value_match = re.search(r"(\d*)r", year_parts[2])
            year_value = int(year_value_match.group(1))

            # fmt: off
            if year_parts[1] in ["BIT", "BITP"]:
                return "4BIT+" if year_value >= 4 else f"{year_value}BIT"
            elif year_parts[1] in ["BCH", "CZV"]:
                return "1BIT"  # TODO: fix erasmus students (BCH)
            elif year_parts[1] in [
                "MBS", "MBI", "MIS", "MIN", "MMI", "MMM", "MGM", "MGMe", "MPV", "MSK",
                "NADE", "NBIO", "NGRI", "NNET", "NVIZ", "NCPS", "NSEC", "NEMB", "NHPC",
                "NISD", "NIDE", "NISY", "NMAL", "NMAT", "NSEN", "NVER", "NSPE", "MGH"
            ]:
                return "3MIT+" if year_value >= 3 else f"{year_value}MIT"
            elif year_parts[1] in ["DVI4", "DRH", "DITP"]:
                return "PhD+"
            # fmt: on
        elif "FEKT" in year_parts:  # FEKT student
            return "VUT"
        elif len(year_parts) == 1 and year_parts[0] == "MUNI":  # Maybe MUNI?
            return "MUNI"

        return None

    # Deprecated. TODO Refactor to interactions.
    async def verify(self, message):
        """ "Verify if VUT login is from database"""
        if len(str(message.content).split(" ")) != 3:
            await message.channel.send(Messages.verify_verify_format)
            return

        login = str(message.content).split(" ")[1]
        code = str(message.content).split(" ")[2]

        # Check if the user doesn't have the verify role
        # otherwise they wouldn't need to verify, right?
        if not await self.has_role(message.author, config.verification_role):
            # Some of them will use 'xlogin00' as stated in help
            # yet again, cuz they dumb
            if login == "xlogin00":
                await self.send_xlogin_info(message)
                return
            # Same here
            if code == "kód" or code == "[kód]":
                guild = self.bot.get_guild(config.guild_id)
                fp = await guild.fetch_emoji(585915845146968093)
                await message.channel.send(
                    utils.fill_message(
                        "verify_verify_dumbshit", user=message.author.id, emote=str(fp)
                    )
                )
                return

            new_user = self.repo.get_user(login)

            if new_user is not None:
                # Check the code
                if code != new_user.code:
                    await message.channel.send(
                        utils.fill_message(
                            "verify_verify_wrong_code", user=message.author.id
                        )
                    )

                    await self.log_verify_fail(message, "Verify (with code)")
                    return

                # Try and transform the year into the role name
                year = self.transform_year(new_user.year)

                if year is None:
                    msg = utils.fill_message(
                        "verify_verify_manual",
                        user=message.author.id,
                        admin=config.admin_ids[0],
                        year=str(new_user.year),
                    )
                    await message.channel.send(msg)

                    await self.log_verify_fail(
                        message, "Verify (with code) (Invalid year)"
                    )
                    return

                try:
                    # Get server verify role
                    verify = disnake.utils.get(
                        message.guild.roles, name=config.verification_role
                    )
                    year = disnake.utils.get(message.guild.roles, name=year)
                    member = message.author
                except AttributeError:
                    # jsme v PM
                    guild = self.bot.get_guild(config.guild_id)
                    verify = disnake.utils.get(
                        guild.roles, name=config.verification_role
                    )
                    year = disnake.utils.get(guild.roles, name=year)
                    member = guild.get_member(message.author.id)

                await member.add_roles(verify)
                await member.add_roles(year)

                self.repo.save_verified(login, message.author.id)

                try:
                    await member.send(
                        utils.fill_message(
                            "verify_verify_success", user=message.author.id
                        )
                    )

                    await member.send(Messages.verify_post_verify_info)
                except disnake.errors.Forbidden:
                    if login[0] == "x":
                        self.send_mail_verified(f"{login}@stud.fit.vutbr.cz", member)
                    else:
                        self.send_mail_verified(f"{login}@mail.muni.cz", member)

                if message.channel.type is not disnake.ChannelType.private:
                    await message.channel.send(
                        utils.fill_message(
                            "verify_verify_success", user=message.author.id
                        )
                    )
            else:
                msg = utils.fill_message(
                    "verify_verify_not_found",
                    user=message.author.id,
                    admin=config.admin_ids[0],
                )
                await message.channel.send(msg)

                await self.log_verify_fail(
                    message, "Verify (with code) - Not exists in DB"
                )
        else:
            await message.channel.send(
                utils.fill_message(
                    "verify_already_verified",
                    user=message.author.id,
                    admin=config.admin_ids[0],
                )
            )

        try:
            await message.delete()
        except disnake.errors.Forbidden:
            return

    async def log_verify_fail(
        self, inter: disnake.ApplicationCommand, phase: str, data: str
    ):
        embed = disnake.Embed(title="Neúspěšný pokus o verify", color=0xEEE657)
        embed.add_field(name="User", value=utils.generate_mention(inter.user.id))
        embed.add_field(name="Verify phase", value=phase)
        embed.add_field(name="Data", value=data, inline=False)
        await self.bot.get_channel(config.log_channel).send(embed=embed)

    async def send_xlogin_info(self, inter: disnake.ApplicationCommandInteraction):
        guild = self.bot.get_guild(config.guild_id)
        fp = await guild.fetch_emoji(585915845146968093)
        await inter.send(
            content=utils.fill_message(
                "verify_send_dumbshit", user=inter.user.id, emote=str(fp)
            )
        )
