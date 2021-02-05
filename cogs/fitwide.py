import datetime
import subprocess
from sqlalchemy.orm.exc import NoResultFound

import discord
from discord.ext import commands


import utils
from config import app_config as config
from features import verification
from repository import user_repo
from repository.database import database, session
from repository.database.verification import Valid_person, Permit
from repository.database.year_increment import User_backup

user_r = user_repo.UserRepository()

config = config.Config
arcas_time = (datetime.datetime.utcnow() -
              datetime.timedelta(hours=config.arcas_delay))


class FitWide(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.verification = verification.Verification(bot, user_r)

    def is_in_modroom(ctx):
        return ctx.message.channel.id == config.mod_room

    @commands.Cog.listener()
    async def on_typing(self, channel, user, when):
        global arcas_time
        if arcas_time + datetime.timedelta(hours=config.arcas_delay) <\
           when and config.arcas_id == user.id:
            arcas_time = when
            gif = discord.Embed()
            gif.set_image(url="https://i.imgur.com/v2ueHcl.gif")
            await channel.send(embed=gif)

    @commands.cooldown(rate=2, per=20.0, type=commands.BucketType.user)
    @commands.check(utils.helper_plus)
    @commands.command()
    async def rolehoarders(self, ctx, limit=config.rolehoarder_default_limit):
        guild = self.bot.get_guild(config.guild_id)

        found_members = []
        for member in guild.members:
            role_count = 0
            for role in member.roles:
                if role.name.lower() in config.subjects:
                    role_count += 1
            if role_count >= limit:
                found_members.append((member, role_count))

        msg = ""
        if len(found_members) == 0:
            msg = "Žádné jsem nenašel :slight_smile:"
        else:
            found_members.sort(key=lambda x: x[1], reverse=True)
            for i, (member, role_count) in enumerate(found_members):
                line = "{index}) <@{id}> - {count}\n".format(index=i+1, id=member.id, count=role_count)
                if len(line) + len(msg) >= 2000:
                    await ctx.send(msg)
                    msg = line
                else:
                    msg += line

        await ctx.send(msg)

    @commands.cooldown(rate=2, per=20.0, type=commands.BucketType.user)
    @commands.check(utils.is_bot_admin)
    @commands.command()
    async def role_check(self, ctx, p_verified: bool = True,
                         p_move: bool = False, p_status: bool = True,
                         p_role: bool = True, p_zapis: bool = False,
                         p_debug: bool = True):
        guild = self.bot.get_guild(config.guild_id)
        members = guild.members

        verify = discord.utils.get(guild.roles, name="Verify")
        host = discord.utils.get(guild.roles, name="Host")
        bot = discord.utils.get(guild.roles, name="Bot")
        poradce = discord.utils.get(guild.roles, name="Poradce")
        dropout = discord.utils.get(guild.roles, name="Dropout")
        vut = discord.utils.get(guild.roles, name="VUT")

        verified = [member for member in members
                    if verify in member.roles and
                    host not in member.roles and
                    bot not in member.roles and
                    poradce not in member.roles and
                    vut not in member.roles]

        permited = session.query(Permit)
        permited_ids = [int(person.discord_ID) for person in permited]

        years = ["0BIT", "1BIT", "2BIT", "3BIT", "4BIT+",
                 "0MIT", "1MIT", "2MIT", "3MIT+", "Dropout"]

        year_roles = {year: discord.utils.get(guild.roles, name=year) for year in years}

        weird_members = {year_y: {year_x: [] for year_x in year_roles.values()}
                         for year_y in year_roles.values()}

        for member in verified:
            if member.id not in permited_ids:
                if p_verified:
                    await ctx.send("Ve verified databázi jsem nenašel: " +
                                   utils.generate_mention(member.id))
            else:
                try:
                    login = session.query(Permit).\
                        filter(Permit.discord_ID == str(member.id)).one().login

                    person = session.query(Valid_person).\
                        filter(Valid_person.login == login).one()
                except NoResultFound:
                    continue

                if person.status != 0:
                    if p_status:
                        await ctx.send("Status nesedí u: " + login)

                year = self.verification.transform_year(person.year)
                
                if year is None:
                    year = "Dropout"

                correct_role = discord.utils.get(guild.roles, name=year)

                if correct_role not in member.roles:
                    for role_name, role in year_roles.items():
                        if role in member.roles and correct_role in weird_members[role].keys():
                            weird_members[role][correct_role].append(member)
                            break
                    else:
                        await ctx.send(f"{utils.generate_mention(member.id)} by mel "
                                       f"mit prej `{year}`")

        for source_role, target_data in weird_members.items():
            for target_role, target_members in target_data.items():
                if len(target_members) == 0:
                    continue
                source_year = source_role.name
                target_year = target_role.name
                target_ids = [member.id for member in target_members]
                if p_zapis and \
                   (("BIT" in source_year and "BIT" in target_year) or \
                   ("MIT" in source_year and "MIT" in target_year)) and \
                   int(source_year[0]) == int(target_year[0]) + 1:
                    message_prefix = f"Vypada ze do dalsiho rocniku se nezapsali (protoze na merlinovi maji {target_year}): "
                    await self.send_masstag_messages(ctx, message_prefix, target_ids)
                elif p_move and (
                    # presun bakalaru do 1MIT
                    ("BIT" in source_year and target_year == "1MIT") or
                    target_year == "Dropout"):
                    await ctx.send(f"Přesouvám techle {len(target_members)} lidi z "
                                   f"{source_year} do {target_year}:")
                    await self.send_masstag_messages(ctx, "", target_ids)
                    if p_debug:
                        await ctx.send(f"jk, debug mode")
                    else:
                        for member in target_members:
                            await member.add_roles(target_role)
                            await member.remove_roles(source_role)
                elif p_role:
                    await ctx.send(f"Nasel jsem {len(target_members)} lidi kteri maji na merlinovi "
                                   f"{target_year} ale roli {source_year}:")
                    await self.send_masstag_messages(ctx, "", target_ids)

        await ctx.send("Done")

    async def send_masstag_messages(self, ctx, prefix, target_ids):
        messages = []
        message = prefix
        for index in range(len(target_ids)):
            # 35 sounds like a safe amount of tags per message
            if index % 35 == 0 and index:
                await ctx.send(message)
                message = prefix
            message += utils.generate_mention(target_ids[index])
            message += " "
        await ctx.send(message)
        return

    @commands.cooldown(rate=2, per=20.0, type=commands.BucketType.user)
    @commands.check(utils.is_bot_admin)
    @commands.command()
    async def increment_roles(self, ctx):
        # guild = self.bot.get_guild(config.guild_id)
        guild = ctx.guild

        BIT_names = [str(x) + "BIT" + ("+" if x == 4 else "")
                     for x in range(5)]
        BIT = [discord.utils.get(guild.roles, name=role_name)
               for role_name in BIT_names]

        MIT_names = [str(x) + "MIT" + ("+" if x == 3 else "")
                     for x in range(4)]
        MIT = [discord.utils.get(guild.roles, name=role_name)
               for role_name in MIT_names]

        for member in BIT[3].members:
            await member.add_roles(BIT[4])
        for member in MIT[2].members:
            await member.add_roles(MIT[3])

        BIT_colors = [role.color for role in BIT]
        await BIT[3].delete()
        await BIT[2].edit(name="3BIT", color=BIT_colors[3])
        await BIT[1].edit(name="2BIT", color=BIT_colors[2])
        await BIT[0].edit(name="1BIT", color=BIT_colors[1])
        bit0 = await guild.create_role(name='0BIT', color=BIT_colors[0])
        await bit0.edit(position=BIT[0].position - 1)

        MIT_colors = [role.color for role in MIT]
        await MIT[2].delete()
        await MIT[1].edit(name="2MIT", color=MIT_colors[2])
        await MIT[0].edit(name="1MIT", color=MIT_colors[1])
        mit0 = await guild.create_role(name='0MIT', color=MIT_colors[0])
        await mit0.edit(position=MIT[0].position - 1)

        general_names = [str(x) + "bit-general" for x in range(4)]
        terminy_names = [str(x) + "bit-terminy" for x in range(1, 3)]
        general_channels = [discord.utils.get(guild.channels,
                                              name=channel_name)
                            for channel_name in general_names]
        terminy_channels = [discord.utils.get(guild.channels,
                                              name=channel_name)
                            for channel_name in terminy_names]

        # move names
        await general_channels[3].edit(name="4bit-general")
        await general_channels[2].edit(name="3bit-general")
        await general_channels[1].edit(name="2bit-general")
        await general_channels[0].edit(name="1bit-general")
        # create 0bit-general
        overwrites = {
            guild.default_role:
                discord.PermissionOverwrite(read_messages=False),
            discord.utils.get(guild.roles, name="0BIT"):
                discord.PermissionOverwrite(read_messages=True,
                                            send_messages=True)
        }
        await guild.create_text_channel(
            '0bit-general', overwrites=overwrites,
            category=general_channels[0].category,
            position=general_channels[0].position - 1
        )
        # give 0mit access to mit-general
        mit_general = discord.utils.get(guild.channels,
                                        name="mit-general")
        await mit_general.set_permissions(mit0, read_messages=True)

        # delete 3bit-terminy
        await discord.utils.get(guild.channels, name="3bit-terminy").delete()

        await terminy_channels[1].edit(name="3bit-terminy")
        await terminy_channels[0].edit(name="2bit-terminy")
        # create 1bit-terminy
        overwrites = {
            guild.default_role:
                discord.PermissionOverwrite(read_messages=False),
            discord.utils.get(guild.roles, name="1BIT"):
                discord.PermissionOverwrite(read_messages=True,
                                            send_messages=False)
        }
        await guild.create_text_channel(
            '1bit-terminy', overwrites=overwrites,
            category=terminy_channels[0].category,
            position=terminy_channels[0].position - 1
        )

        # give 4bit perms to the new 3bit terminy
        await terminy_channels[1].set_permissions(
            discord.utils.get(guild.roles, name="4BIT+"),
            read_messages=True, send_messages=False
        )

        # Give people the correct mandatory classes after increment
        semester_names = [str(x) + ". Semestr" for x in range(1, 6)]
        semester = [discord.utils.get(guild.categories, name=semester_name)
                    for semester_name in semester_names]
        await semester[0].set_permissions(discord.utils.get(guild.roles,
                                                            name="1BIT"),
                                          read_messages=True)
        await semester[0].set_permissions(discord.utils.get(guild.roles,
                                                            name="2BIT"),
                                          overwrite=None)
        await semester[1].set_permissions(discord.utils.get(guild.roles,
                                                            name="1BIT"),
                                          read_messages=True)
        await semester[1].set_permissions(discord.utils.get(guild.roles,
                                                            name="2BIT"),
                                          overwrite=None)
        await semester[2].set_permissions(discord.utils.get(guild.roles,
                                                            name="2BIT"),
                                          read_messages=True)
        await semester[2].set_permissions(discord.utils.get(guild.roles,
                                                            name="3BIT"),
                                          overwrite=None)
        await semester[3].set_permissions(discord.utils.get(guild.roles,
                                                            name="2BIT"),
                                          read_messages=True)
        await semester[3].set_permissions(discord.utils.get(guild.roles,
                                                            name="3BIT"),
                                          overwrite=None)
        await semester[4].set_permissions(discord.utils.get(guild.roles,
                                                            name="3BIT"),
                                          read_messages=True)

        # Warning: This was somehow ran before the semester permissions changed
        # So just keep in mind that weird shit happens
        for category in semester:
            for channel in category.channels:
                await channel.edit(sync_permissions=True)

        # skolni-info override
        skolni_info = discord.utils.get(guild.channels,
                                        name="skolni-info")
        await skolni_info.set_permissions(bit0, read_messages=True)
        await skolni_info.set_permissions(mit0, read_messages=True)

        await ctx.send('Holy fuck, všechno se povedlo, '
                       'tak zase za rok <:Cauec:602052606210211850>')

    @commands.cooldown(rate=2, per=20.0, type=commands.BucketType.user)
    @commands.check(is_in_modroom)
    @commands.command()
    async def update_db(self, ctx, convert_0xit: bool = False):
        with open("merlin-latest", "r") as f:
            data = f.readlines()

        found_people = []
        found_logins = []
        new_logins = []
        login_results = session.query(Valid_person.login).all()
        # Use unpacking on results
        old_logins = [value for value, in login_results]

        for line in data:
            line = line.split(":")
            login = line[0]
            name = line[4].split(",", 1)[0]
            try:
                year = line[4].split(",")[1]
            except IndexError:
                continue

            if convert_0xit and year.endswith("1r"):
                person = session.query(Valid_person).\
                    filter(Valid_person.login == login).\
                    one_or_none()
                if person is not None and person.year.endswith("0r"):
                    year = year.replace("1r", "0r")

            found_people.append(Valid_person(login=login, year=year,
                                             name=name))
            found_logins.append(login)

        for login in found_logins:
            if login not in old_logins:
                new_logins.append(login)

        await ctx.send(f"Našel jsem {len(new_logins)} nových loginů.")

        for person in found_people:
            session.merge(person)

        cnt_new = 0
        for person in session.query(Valid_person):
            if person.login not in found_logins:
                try:
                    # check for muni
                    int(person.login)
                    person.year = "MUNI"
                except ValueError:
                    person.year = "dropout"
            elif convert_0xit and person.login in new_logins:
                if person.year.endswith("1r"):
                    person.year = person.year.replace("1r", "0r")
                    cnt_new += 1

        session.commit()

        await ctx.send("Aktualizace databáze proběhla úspěšně.")
        if convert_0xit:
            await ctx.send(f"Debug: Našel jsem {cnt_new} nových prvaků.")

    @commands.cooldown(rate=2, per=20.0, type=commands.BucketType.user)
    @commands.check(is_in_modroom)
    @commands.command()
    async def get_db(self, ctx):
        process = subprocess.Popen(["ssh", "merlin"], stdout=subprocess.PIPE)
        try:
            output, error = process.communicate(timeout=15)
            if error:
                await ctx.send("Stažené databáze nějak nefunguje.")
                return
        except TimeoutExpired:
            await ctx.send("Timeout při stahování databáze.")
            return
        with open("merlin-latest", "w") as f:
            f.write(output.decode("utf-8"))
        await ctx.send("Stažení databáze proběhlo úspěšně.")

    @commands.cooldown(rate=2, per=20.0, type=commands.BucketType.user)
    @commands.check(is_in_modroom)
    @commands.command()
    async def get_users_login(self, ctx, member: discord.Member):
        result = session.query(Permit).\
            filter(Permit.discord_ID == str(member.id)).one_or_none()

        if result is None:
            await ctx.send("Uživatel není v databázi.")
            return

        person = session.query(Valid_person).\
            filter(Valid_person.login == result.login).one_or_none()

        if person is None:
            await ctx.send(result.login)
            return

        await ctx.send(("Login: `{p.login}`\nJméno: `{p.name}`\n"
                        "Ročník: `{p.year}`").format(p=person))

    @commands.cooldown(rate=2, per=20.0, type=commands.BucketType.user)
    @commands.check(is_in_modroom)
    @commands.command()
    async def get_logins_user(self, ctx, login):
        result = session.query(Permit).\
            filter(Permit.login == login).one_or_none()

        if result is None:
            person = session.query(Valid_person).\
                filter(Valid_person.login == login).one_or_none()
            if person is None:
                await ctx.send("Uživatel není v databázi možných loginů.")
            else:
                await ctx.send(("Login: `{p.login}`\nJméno: `{p.name}`\n"
                                "Ročník: `{p.year}`\nNení na serveru."
                                ).format(p=person))
        else:
            await ctx.send(utils.generate_mention(result.discord_ID))

    @commands.cooldown(rate=2, per=20.0, type=commands.BucketType.user)
    @commands.check(is_in_modroom)
    @commands.command()
    async def reset_login(self, ctx, login):

        result = session.query(Valid_person).\
            filter(Valid_person.login == login).one_or_none()
        if result is None:
            await ctx.send("To není validní login.")
        else:
            session.query(Permit).\
                filter(Permit.login == login).delete()
            result.status = 1
            session.commit()
            await ctx.send("Hotovo.")

    @commands.cooldown(rate=2, per=20.0, type=commands.BucketType.user)
    @commands.check(is_in_modroom)
    @commands.command()
    async def connect_login_to_user(self, ctx, login, member: discord.Member):

        result = session.query(Valid_person).\
            filter(Valid_person.login == login).one_or_none()
        if result is None:
            await ctx.send("To není validní login.")
        else:
            session.add(Permit(login=login, discord_ID=str(member.id)))
            result.status = 0
            session.commit()
            await ctx.send("Hotovo.")

    @get_users_login.error
    @reset_login.error
    @get_logins_user.error
    @role_check.error
    @increment_roles.error
    @update_db.error
    @get_db.error
    async def fitwide_checks_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send('Nothing to see here comrade. ' +
                           '<:KKomrade:484470873001164817>')


def setup(bot):
    bot.add_cog(FitWide(bot))
