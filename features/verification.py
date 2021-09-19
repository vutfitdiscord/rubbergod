import random
import smtplib
import ssl
import string
import re

import discord
from discord import Member
from discord.ext.commands import Bot

import utils
from config.app_config import Config
from config.messages import Messages
from features.base_feature import BaseFeature
from repository.user_repo import UserRepository, VerifyStatus


class Verification(BaseFeature):

    def __init__(self, bot: Bot, user_repository: UserRepository):
        super().__init__(bot)
        self.repo = user_repository

    def send_mail(self, receiver_email, contents):
        password = Config.email_pass
        port = Config.email_smtp_port
        context = ssl.create_default_context()
        sender_email = Config.email_addr
        subject = "FIT Discord verifikace"
        mail_content = 'Subject: {}\n\n{}'.format(subject,
                                                  contents)

        with smtplib.SMTP_SSL(Config.email_smtp_server, port,
                              context=context) as server:
            server.login(Config.email_name, password)
            server.sendmail(sender_email, receiver_email, mail_content)

    def send_mail_verified(self, receiver_email, user):
        """Send mail with instructions in case of blocked DMs"""
        password = Config.email_pass
        port = Config.email_smtp_port
        context = ssl.create_default_context()
        sender_email = Config.email_addr
        subject = f"{user} {Messages.verify_verify_success_mail}"
        mail_content = f'Subject: {subject}\n\n{Messages.verify_post_verify_info_mail}'

        with smtplib.SMTP_SSL(Config.email_smtp_server, port,
                              context=context) as server:
            server.login(Config.email_name, password)
            server.sendmail(sender_email, receiver_email, mail_content)

    async def has_role(self, user, role_name):
        if type(user) == Member:
            return utils.has_role(user, role_name)
        else:
            guild = await self.bot.fetch_guild(Config.guild_id)
            member = await guild.fetch_member(user.id)
            return utils.has_role(member, role_name)

    async def gen_code_and_send_mail(self, message, login, mail_postfix):
        # Generate a verification code
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=20))

        email_message = Config.default_prefix + "verify "
        email_message += login + " " + code

        self.send_mail(login + mail_postfix, email_message)

        # Save the newly generated code into the database
        self.repo.save_sent_code(login, code)

        await message.channel.send(utils.fill_message("verify_send_success",
                                                      user=message.author.id, mail=mail_postfix))

    async def send_code(self, message):
        if len(str(message.content).split(" ")) != 2:
            await message.channel.send(Messages.verify_send_format)
            return

        # Check if the user doesn't have the verify role
        if not await self.has_role(message.author, Config.verification_role):
            login = str(message.content).split(" ")[1]

            # Some of them will use 'xlogin00' as stated in help,
            # cuz they dumb
            if login == "xlogin00":
                await self.send_xlogin_info(message)
                return
            if login[0] == 'x':
                # VUT
                # Check if the login we got is in the database
                user = self.repo.get_user_by_login(login)

                if user is None:
                    msg = utils.fill_message("verify_unknown_login",
                                             user=message.author.id, admin=Config.admin_ids[0])
                    await message.channel.send(msg)
                    await self.log_verify_fail(message, 'getcode (xlogin) - Unknown login')
                elif user is not None and user.status != VerifyStatus.Unverified.value:
                    msg = utils.fill_message(
                        "verify_step_done", user=message.author.id, admin=Config.admin_ids[0])
                    await message.channel.send(msg)
                    await self.log_verify_fail(message, 'getcode (xlogin) - Invalid verify state')
                else:
                    await self.gen_code_and_send_mail(message, login, "@stud.fit.vutbr.cz")
            else:
                # MUNI
                try:
                    int(login)
                except ValueError:
                    msg = utils.fill_message("invalid_login", user=message.author.id,
                                             admin=Config.admin_ids[0])
                    await message.channel.send(msg)
                    await self.log_verify_fail(message, 'getcode (MUNI)')

                    try:
                        await message.delete()
                        return
                    except discord.errors.Forbidden:
                        return

                user = self.repo.get_user_by_login(login)

                if user is not None and user.status != VerifyStatus.Unverified.value:
                    msg = utils.fill_message(
                        "verify_step_done", user=message.author.id, admin=Config.admin_ids[0])
                    await message.channel.send(msg)
                    await self.log_verify_fail(message, 'getcode (MUNI) - Verified')
                    return

                if self.repo.get_user(login, status=VerifyStatus.Unverified.value) is None:
                    self.repo.add_user(login, "MUNI", status=VerifyStatus.Unverified.value)
                await self.gen_code_and_send_mail(message, login, "@mail.muni.cz")
        else:
            await message.channel.send(utils.fill_message("verify_already_verified",
                                                          user=message.author.id, admin=Config.admin_ids[0]))
        try:
            await message.delete()
        except discord.errors.HTTPException:
            return

    @staticmethod
    def transform_year(raw_year: str):
        """Parses year string originally from /etc/passwd into a role name"""

        if raw_year.lower() == "dropout":
            return "Dropout"

        year_parts = list(filter(lambda x: len(x.strip()) > 0, raw_year.split()))

        if year_parts[0] == "FIT":  # FIT student, or some VUT student.
            if len(year_parts) != 3:  # ['FIT'], ['FIT', '1r'], .... Who knows. Other faculty students, dropouts, ...
                return None

            year_value_match = re.search(r'(\d*)r', year_parts[2])
            year_value = int(year_value_match.group(1))

            if year_parts[1] in ["BIT", "BITP"]:
                return "4BIT+" if year_value >= 4 else f"{year_value}BIT"
            elif year_parts[1] in ["BCH", "CZV"]:
                return "1BIT"  # TODO: fix erasmus students (BCH)
            elif year_parts[1] in ["MBS", "MBI", "MIS", "MIN", "MMI", "MMM", "MGM", "MGMe",
                                   "MPV", "MSK", "NADE", "NBIO", "NGRI", "NNET", "NVIZ", "NCPS",
                                   "NSEC", "NEMB", "NHPC", "NISD", "NIDE", "NISY", "NMAL", "NMAT",
                                   "NSEN", "NVER", "NSPE", "MGH"]:
                return '3MIT+' if year_value >= 3 else f'{year_value}MIT'
            elif year_parts[1] in ["DVI4", "DRH", "DITP"]:
                return 'PhD+'
        elif "FEKT" in year_parts:  # FEKT student
            return "VUT"
        elif len(year_parts) == 1 and year_parts[0] == "MUNI":  # Maybe MUNI?
            return "MUNI"

        return None

    async def verify(self, message):
        """"Verify if VUT login is from database"""
        if len(str(message.content).split(" ")) != 3:
            await message.channel.send(Messages.verify_verify_format)
            return

        login = str(message.content).split(" ")[1]
        code = str(message.content).split(" ")[2]

        # Check if the user doesn't have the verify role
        # otherwise they wouldn't need to verify, right?
        if not await self.has_role(message.author, Config.verification_role):
            # Some of them will use 'xlogin00' as stated in help
            # yet again, cuz they dumb
            if login == "xlogin00":
                await self.send_xlogin_info(message)
                return
            # Same here
            if code == "kód" or code == "[kód]":
                guild = self.bot.get_guild(Config.guild_id)
                fp = await guild.fetch_emoji(585915845146968093)
                await message.channel.send(utils.fill_message("verify_verify_dumbshit",
                                                              user=message.author.id, emote=str(fp)))
                return

            new_user = self.repo.get_user(login)

            if new_user is not None:
                # Check the code
                if code != new_user.code:
                    await message.channel.send(utils.fill_message("verify_verify_wrong_code",
                                                                  user=message.author.id))

                    await self.log_verify_fail(message, 'Verify (with code)')
                    return

                # Try and transform the year into the role name
                year = self.transform_year(new_user.year)

                if year is None:
                    msg = utils.fill_message("verify_verify_manual", user=message.author.id,
                                             admin=Config.admin_ids[0], year=str(new_user.year))
                    await message.channel.send(msg)

                    await self.log_verify_fail(message, 'Verify (with code) (Invalid year)')
                    return

                try:
                    # Get server verify role
                    verify = discord.utils.get(message.guild.roles, name=Config.verification_role)
                    year = discord.utils.get(message.guild.roles, name=year)
                    member = message.author
                except AttributeError:
                    # jsme v PM
                    guild = self.bot.get_guild(Config.guild_id)
                    verify = discord.utils.get(guild.roles, name=Config.verification_role)
                    year = discord.utils.get(guild.roles, name=year)
                    member = guild.get_member(message.author.id)

                await member.add_roles(verify)
                await member.add_roles(year)

                self.repo.save_verified(login, message.author.id)

                try:
                    await member.send(utils.fill_message("verify_verify_success",
                                                        user=message.author.id))

                    await member.send(Messages.verify_post_verify_info)
                except discord.errors.Forbidden:
                    if login[0] == 'x':
                        self.send_mail_verified(f"{login}@stud.fit.vutbr.cz", member)
                    else:
                        self.send_mail_verified(f"{login}@mail.muni.cz", member)

                if message.channel.type is not discord.ChannelType.private:
                    await message.channel.send(utils.fill_message("verify_verify_success",
                                                                  user=message.author.id))
            else:
                msg = utils.fill_message("verify_verify_not_found", user=message.author.id,
                                         admin=Config.admin_ids[0])
                await message.channel.send(msg)

                await self.log_verify_fail(message, 'Verify (with code) - Not exists in DB')
        else:
            await message.channel.send(utils.fill_message("verify_already_verified",
                                                          user=message.author.id, admin=Config.admin_ids[0]))

        try:
            await message.delete()
        except discord.errors.Forbidden:
            return

    async def log_verify_fail(self, message: discord.Message, phase: str):
        embed = discord.Embed(title="Neúspěšný pokus o verify", color=0xeee657)
        embed.add_field(name="User", value=utils.generate_mention(message.author.id))
        embed.add_field(name='Verify phase', value=phase)
        embed.add_field(name="Message", value=message.content, inline=False)
        channel = self.bot.get_channel(Config.log_channel)
        await channel.send(embed=embed)

    async def send_xlogin_info(self, message: discord.Message):
        guild = self.bot.get_guild(Config.guild_id)
        fp = await guild.fetch_emoji(585915845146968093)
        await message.channel.send(utils.fill_message("verify_send_dumbshit",
                                                      user=message.author.id, emote=str(fp)))
