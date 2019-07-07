from repository.base_repository import BaseRepository
import discord
import random
import ssl
import string
import smtplib


class Verification(BaseRepository):

    def __init__(self, client, utils, user):
        self.client = client
        self.utils = utils
        self.user = user

    async def send_code(self, message):
        if len(str(message.content).split(" ")) != 2:
            await message.channel.send(
                    "Očekávám 1 argument (login)\n")
            return

        if not self.user.has_role(message, self.config.verification_role):
            if str(message.content).split(" ")[1] == "xlogin00":
                guild = self.client.get_guild(self.config.guild_id)
                fp = await guild.fetch_emoji(585915845146968093)
                await message.channel.send("Tvuj login {} {}"
                                           .format(str(fp),
                                                   self.utils.generate_mention(
                                                       message.author.id)))
                return

            db_record = self.user.find_login_to_mail(message)
            if db_record:
                # get server permit role

                code = ''.join(random.choices(string.ascii_uppercase +
                                              string.digits, k=20))

                login = str(message.content).split(" ")[1]
                email_message = "!verify " + login + " " + code
                password = self.config.email_pass
                port = 465
                context = ssl.create_default_context()
                sender_email = "toasterrubbergod@gmail.com"
                receiver_email = login + "@stud.fit.vutbr.cz"
                subject = "FIT Discord verifikace"
                mail_content = 'Subject: {}\n\n{}'.format(subject,
                                                          email_message)

                with smtplib.SMTP_SSL("smtp.gmail.com", port,
                                      context=context) as server:
                    server.login("toasterrubbergod@gmail.com", password)
                    server.sendmail(sender_email, receiver_email, mail_content)

                self.user.save_mail(message, code)

                await message.channel.send(
                        "Kód byl odeslán na tvůj mail "
                        "(@stud.fit.vutbr.cz)! {}\n"
                        "Pro verifikaci použij:\n"
                        "!verify xlogin00 kód"
                        .format(self.utils.generate_mention(
                                    message.author.id)))
            else:
                await message.channel.send(
                        "Login nenalezen nebo jsi již "
                        "prošel tímhle krokem {} {}"
                        .format(self.utils.generate_mention(
                                    message.author.id),
                                self.utils.generate_mention(
                                    self.config.admin_id)))
        else:
            await message.channel.send("Už si byl verifikován {} {}"
                                       .format(self.utils.generate_mention(
                                                   message.author.id),
                                               self.utils.generate_mention(
                                               self.config.admin_id)))
        try:
            await message.delete()
        except discord.errors.Forbidden:
            return

    async def verify(self, message):
        """"Verify if VUT login is from database"""
        if len(str(message.content).split(" ")) != 3:
            await message.channel.send(
                    "Očekávám 2 argumenty (login a kód)\n" +
                    "Pro získaní kódu použij `!getcode xlogin00`")
            return

        if not self.user.has_role(message, self.config.verification_role):
            if str(message.content).split(" ")[1] == "xlogin00":
                guild = self.client.get_guild(self.config.guild_id)
                fp = await guild.fetch_emoji(585915845146968093)
                await message.channel.send("Tvůj login {} {}"
                                           .format(str(fp),
                                                   self.utils.generate_mention(
                                                       message.author.id)))
                return
            if str(message.content).split(" ")[2] == "kód":
                guild = self.client.get_guild(self.config.guild_id)
                fp = await guild.fetch_emoji(585915845146968093)
                await message.channel.send("Kód který ti přišel na mail {} {}"
                                           .format(str(fp),
                                                   self.utils.generate_mention(
                                                       message.author.id)))
                return

            db_record = self.user.find_login(message)
            if db_record:
                db_record = db_record[2].split()
                year = None
                if len(db_record) == 3:
                    if db_record[0] == "FIT":
                        db_record[2] = int(db_record[2][:-1])
                        if db_record[1] == "BIT":
                            year = "BIT"
                            if db_record[2] < 4:
                                year = str(db_record[2]) + year
                            else:
                                year = "4BIT+"
                        elif db_record[1] in ["MBS", "MBI", "MIS", "MIN",
                                              "MMI", "MMM", "MGM", "MGMe",
                                              "MPV", "MSK"]:
                            year = "MIT"
                            if db_record[2] < 3:
                                year = str(db_record[2]) + year
                            else:
                                year = "3MIT+"
                        elif db_record[1] == "DVI4":
                            year = "PhD+"
                    elif db_record[0] == "FEKT":
                        year = "FEKT"

                if year is None:
                    await message.channel.send(
                        "Čauec {}, nechám {} aby to udělal manuálne\nYear:`{}`"
                        .format(self.utils.generate_mention(
                                    message.author.id),
                                self.utils.generate_mention(
                                    self.config.admin_id),
                                str(db_record)))
                    return

                try:
                    # get server permit role
                    verify = discord.utils.get(
                            message.guild.roles,
                            name=self.config.verification_role)
                    year = discord.utils.get(message.guild.roles, name=year)
                    member = message.author
                except AttributeError:
                    # jsme v PM
                    guild = self.client.get_guild(self.config.guild_id)
                    verify = discord.utils.get(
                                 guild.roles,
                                 name=self.config.verification_role)
                    year = discord.utils.get(guild.roles, name=year)
                    member = guild.get_member(message.author.id)

                await member.add_roles(verify)
                await member.add_roles(year)
                self.user.save_record(message)
                await message.channel.send("Gratuluji, byl si verifikován! {}"
                                           .format(self.utils.generate_mention(
                                                       message.author.id)))
            else:
                await message.channel.send(
                        "Login nenalezen nebo jsi jiz "
                        "prosel timhle krokem {} {}"
                        .format(self.utils.generate_mention(
                                    message.author.id),
                                self.utils.generate_mention(
                                    self.config.admin_id)))
        else:
            await message.channel.send("Už si byl verifikován {} {}"
                                       .format(self.utils.generate_mention(
                                                   message.author.id),
                                               self.utils.generate_mention(
                                                   self.config.admin_id)))
        try:
            await message.delete()
        except discord.errors.Forbidden:
            return
