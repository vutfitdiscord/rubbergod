"""
Cog implementing management of year roles and database of user logins.
"""

import subprocess

import disnake
from disnake.ext import commands
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

import utils
from cogs.base import Base
from config import cooldowns
from config.messages import Messages
from database import session
from database.verification import PermitDB, ValidPersonDB
from features import verification
from permissions import permission_check, room_check


class FitWide(Base, commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.verification = verification.Verification(bot)

    @cooldowns.default_cooldown
    @commands.check(permission_check.is_bot_admin)
    @commands.command()
    async def role_check(
        self,
        ctx,
        p_verified: bool = True,
        p_move: bool = False,
        p_status: bool = True,
        p_role: bool = True,
        p_zapis: bool = False,
        p_debug: bool = True,
    ):
        guild = self.bot.get_guild(self.config.guild_id)
        members = guild.members

        verify = disnake.utils.get(guild.roles, name="Verify")
        host = disnake.utils.get(guild.roles, name="Host")
        bot = disnake.utils.get(guild.roles, name="Bot")
        poradce = disnake.utils.get(guild.roles, name="Poradce")
        dropout = disnake.utils.get(guild.roles, name="Dropout")
        survivor = disnake.utils.get(guild.roles, name="Survivor")
        king = disnake.utils.get(guild.roles, name="King")
        vut = disnake.utils.get(guild.roles, name="VUT")

        dropout_alternatives = [survivor, king]

        verified = [
            member
            for member in members
            if verify in member.roles
            and host not in member.roles
            and bot not in member.roles
            and poradce not in member.roles
            and vut not in member.roles
        ]

        permited = session.query(PermitDB)
        permited_ids = [int(person.discord_ID) for person in permited]

        years = ["0BIT", "1BIT", "2BIT", "3BIT+", "0MIT", "1MIT", "2MIT+", "Doktorand", "VUT", "Dropout"]

        year_roles = {year: disnake.utils.get(guild.roles, name=year) for year in years}

        weird_members = {
            year_y: {year_x: [] for year_x in year_roles.values()} for year_y in year_roles.values()
        }

        for member in verified:
            if member.id not in permited_ids:
                if p_verified:
                    await ctx.send("Ve verified databázi jsem nenašel: " + utils.generate_mention(member.id))
            else:
                try:
                    login = session.query(PermitDB).filter(PermitDB.discord_ID == str(member.id)).one().login

                    person = session.query(ValidPersonDB).filter(ValidPersonDB.login == login).one()
                except NoResultFound:
                    continue
                except MultipleResultsFound:
                    await ctx.send(f"{member.id} je v permit databazi vickrat?")
                    continue

                if person.status != 0:
                    if p_status:
                        await ctx.send("Status nesedí u: " + login)

                year = self.verification.transform_year(person.year)

                if year is None:
                    year = "Dropout"

                correct_role = disnake.utils.get(guild.roles, name=year)

                if correct_role not in member.roles:
                    for role_name, role in year_roles.items():
                        if role in member.roles and correct_role in weird_members[role].keys():
                            weird_members[role][correct_role].append(member)
                            break
                    else:
                        if not (correct_role == dropout and any(
                            role in member.roles for role in dropout_alternatives
                        )):
                            weird_members[dropout][correct_role].append(member)

        for source_role, target_data in weird_members.items():
            for target_role, target_members in target_data.items():
                if len(target_members) == 0:
                    continue
                source_year = source_role.name
                target_year = target_role.name
                target_ids = [member.id for member in target_members]
                if (
                    p_zapis
                    and (
                        ("BIT" in source_year and "BIT" in target_year)
                        or ("MIT" in source_year and "MIT" in target_year)
                    )
                    and int(source_year[0]) == int(target_year[0]) + 1
                ):
                    message_prefix = (
                        "Vypada ze do dalsiho rocniku se nezapsali "
                        f"(protoze na merlinovi maji {target_year}): "
                    )
                    await self.send_masstag_messages(ctx, message_prefix, target_ids)
                elif p_move and (
                    # presun bakalaru do 1MIT
                    ("BIT" in source_year and target_year == "1MIT")
                    or target_year == "Dropout"
                ):
                    await ctx.send(
                        f"Přesouvám techle {len(target_members)} lidi z {source_year} do {target_year}:"
                    )
                    await self.send_masstag_messages(ctx, "", target_ids)
                    if p_debug:
                        await ctx.send("jk, debug mode")
                    else:
                        for member in target_members:
                            if not (target_role == dropout and any(
                                role in member.roles for role in dropout_alternatives
                            )):
                                await member.add_roles(target_role)
                            await member.remove_roles(source_role)
                elif p_role:
                    await ctx.send(
                        f"Nasel jsem {len(target_members)} lidi kteri maji na merlinovi "
                        f"{target_year} ale roli {source_year}:"
                    )
                    await self.send_masstag_messages(ctx, "", target_ids)

        await ctx.send("Done")

    async def send_masstag_messages(self, ctx, prefix, target_ids):
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

    async def set_channel_permissions_for_new_students(
        self,
        message: disnake.Message,
        guild: disnake.Guild,
        bit0: disnake.Role,
        mit0: disnake.Role,
        bit_terminy_channels: list,
        info_channels: list,
    ) -> None:
        """Set permissions for new 0bit and 0mit roles to see school channels"""
        # Get all semester categories
        categories_names = [
            "1. semestr", "2. semestr", "3. semestr", "4. semestr", "5. semestr",
            "zimni-volitelne", "letni-volitelne", "volitelne",
            "zimni magistersky semestr", "letni magistersky semestr"
        ]
        categories = [
            disnake.utils.get(guild.categories, name=semester_name) for semester_name in categories_names
        ]

        # give 0mit access to mit-general
        mit_general = disnake.utils.get(guild.channels, name="mit-general")
        await mit_general.set_permissions(mit0, read_messages=True)

        mit_channels_names = ["mit-terminy", "mit-info"]
        mit_channels = [
            disnake.utils.get(guild.channels, name=channel_name) for channel_name in mit_channels_names
        ]
        for channel in mit_channels:
            await channel.set_permissions(bit0, read_messages=True)
            await channel.set_permissions(mit0, read_messages=True)

        # Xbit-info channels overwrites
        for channel in info_channels:
            await channel.set_permissions(bit0, read_messages=True)

        # Xbit-terminy overwrites
        for terminy_channel in bit_terminy_channels:
            await terminy_channel.set_permissions(bit0, read_messages=True)

        # for every channel in category set overwrite
        for index, category in enumerate(categories):
            progress_bar = utils.create_bar(index, len(categories))
            await message.edit(f"Přídávám práva pro roomky: {progress_bar}")
            for channel in category.channels:
                await channel.set_permissions(bit0, read_messages=True)
                await channel.set_permissions(mit0, read_messages=True)

        # skolni-info, cvicici-info, stream-links, senat-unie-drby room overwrites
        channel_names = ["skolni-info", "cvicici-info", "stream-links", "senat-unie-drby"]
        channels = [
            disnake.utils.get(guild.channels, name=channel_name) for channel_name in channel_names
        ]
        for channel in channels:
            await channel.set_permissions(bit0, read_messages=True)
            await channel.set_permissions(mit0, read_messages=True)

    @cooldowns.default_cooldown
    @commands.check(permission_check.is_bot_admin)
    @commands.slash_command(name="increment_roles", description=Messages.increment_roles_brief)
    async def increment_roles(self, inter: disnake.ApplicationCommandInteraction):
        await inter.send(Messages.increment_roles_start)
        message = await inter.original_message()
        guild = inter.guild

        BIT_names = ["0BIT", "1BIT", "2BIT", "3BIT+"]
        BIT_roles = [disnake.utils.get(guild.roles, name=role_name) for role_name in BIT_names]

        MIT_names = ["0MIT", "1MIT", "2MIT+"]
        MIT_roles = [disnake.utils.get(guild.roles, name=role_name) for role_name in MIT_names]
        VUT = disnake.utils.get(guild.roles, name="VUT")

        # create 4bit-1mit and add members
        bit4_members = BIT_roles[3].members
        bit4 = await guild.create_role(name="4bit-1mit")
        for index, member in enumerate(bit4_members):
            await member.add_roles(bit4)
            if (index % 50) == 0:
                progress_bar = utils.create_bar(index, len(bit4_members))
                await message.edit(f"Přidávání role 4bit-1mit: {progress_bar}")

        # give 3bit/2mit users 2bit/1mit role
        for index, member in enumerate(BIT_roles[3].members):
            await member.add_roles(BIT_roles[2])
            if (index % 50) == 0:
                progress_bar = utils.create_bar(index, len(BIT_roles[3].members))
                await message.edit(f"Přidávání role 3bit: {progress_bar}")

        for index, member in enumerate(MIT_roles[2].members):
            if (index % 50) == 0:
                progress_bar = utils.create_bar(index, len(MIT_roles[2].members))
                await message.edit(f"Přidávání role 2mit: {progress_bar}")
            await member.add_roles(MIT_roles[1])

        # increment roles and create 0bit and 0mit
        BIT_COLORS = [role.color for role in BIT_roles]
        await BIT_roles[3].delete()
        await BIT_roles[2].edit(name="3BIT+", color=BIT_COLORS[3])
        await BIT_roles[1].edit(name="2BIT", color=BIT_COLORS[2])
        await BIT_roles[0].edit(name="1BIT", color=BIT_COLORS[1])
        BIT_roles.insert(0, await guild.create_role(name="0BIT", color=BIT_COLORS[0]))
        await BIT_roles[0].edit(position=BIT_roles[1].position - 1)

        MIT_COLORS = [role.color for role in MIT_roles]
        await MIT_roles[2].delete()
        await MIT_roles[1].edit(name="2MIT+", color=MIT_COLORS[2])
        await MIT_roles[0].edit(name="1MIT", color=MIT_COLORS[1])
        MIT_roles.insert(0, await guild.create_role(name="0MIT", color=MIT_COLORS[0]))
        await MIT_roles[0].edit(position=MIT_roles[1].position - 1)

        # status update
        await message.edit(Messages.increment_roles_names)

        # get channels by name
        GENERAL_NAMES = ["0bit-general", "1bit-general", "2bit-general", "3bit-general"]
        TERMINY_NAMES = ["1bit-terminy", "2bit-terminy", "3bit-terminy"]
        INFO_NAMES = ["0bit-info", "1bit-info", "2bit-info", "3bit-info"]
        general_channels = [
            disnake.utils.get(guild.channels, name=channel_name) for channel_name in GENERAL_NAMES
        ]
        bit_terminy_channels = [
            disnake.utils.get(guild.channels, name=channel_name) for channel_name in TERMINY_NAMES
        ]
        info_channels = [disnake.utils.get(guild.channels, name=channel_name) for channel_name in INFO_NAMES]

        # increment channel names
        overwrites = {
            guild.default_role: disnake.PermissionOverwrite(read_messages=False),
            bit4: disnake.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        await general_channels[3].edit(name="4bit-1mit-general", overwrites=overwrites)
        await general_channels[2].edit(name="3bit-general")
        await general_channels[1].edit(name="2bit-general")
        await general_channels[0].edit(name="1bit-general")

        # create 0bit-general
        overwrites = {
            guild.default_role: disnake.PermissionOverwrite(read_messages=False),
            disnake.utils.get(guild.roles, name="0BIT"): disnake.PermissionOverwrite(
                read_messages=True, send_messages=True
            ),
        }
        await guild.create_text_channel(
            "0bit-general",
            overwrites=overwrites,
            category=general_channels[0].category,
            position=general_channels[0].position - 1,
        )

        # status update
        await message.edit(Messages.increment_roles_room_names)

        # increment terminy and delete 3bit-terminy
        bit_terminy_channels.pop(2)
        await disnake.utils.get(guild.channels, name="3bit-terminy").delete()
        await bit_terminy_channels[1].edit(name="3bit-terminy")
        await bit_terminy_channels[0].edit(name="2bit-terminy")

        # create 1bit-terminy
        overwrites = {
            guild.default_role: disnake.PermissionOverwrite(
                read_messages=False,
                send_messages=False,
                create_private_threads=False,
                create_public_threads=False
            ),
            disnake.utils.get(guild.roles, name="1BIT"): disnake.PermissionOverwrite(
                read_messages=True
            ),
            BIT_roles[0]: disnake.PermissionOverwrite(read_messages=True),
            BIT_roles[1]: disnake.PermissionOverwrite(read_messages=True),
            BIT_roles[2]: disnake.PermissionOverwrite(read_messages=True),
            BIT_roles[3]: disnake.PermissionOverwrite(read_messages=True),
            VUT: disnake.PermissionOverwrite(read_messages=True),
        }

        terminy_1bit_channel = await guild.create_text_channel(
            "1bit-terminy",
            overwrites=overwrites,
            category=bit_terminy_channels[0].category,
            position=bit_terminy_channels[0].position - 1,
        )
        bit_terminy_channels.insert(0, terminy_1bit_channel)

        await self.set_channel_permissions_for_new_students(
            message, guild, BIT_roles[0], MIT_roles[0], bit_terminy_channels, info_channels
        )

        await inter.edit_original_response(Messages.increment_roles_success)

    @cooldowns.default_cooldown
    @commands.check(room_check.is_in_modroom)
    @commands.command()
    async def update_db(self, ctx, convert_0xit: bool = False):
        with open("merlin-latest", "r") as f:
            data = f.readlines()

        found_people = []
        found_logins = []
        new_logins = []
        login_results = session.query(ValidPersonDB.login).all()
        # Use unpacking on results
        old_logins = [value for value, in login_results]

        for line in data:
            line = line.split(":")
            login = line[0]
            name = line[4].split(",", 1)[0]
            try:
                year_fields = line[4].split(",")[1].split(" ")
                year = " ".join(year_fields if "mail=" not in year_fields[-1] else year_fields[:-1])
                mail = year_fields[-1].replace("mail=", "") if "mail=" in year_fields[-1] else None
            except IndexError:
                continue

            if convert_0xit and year.endswith("1r"):
                person = session.query(ValidPersonDB).filter(ValidPersonDB.login == login).one_or_none()
                if person is not None and person.year.endswith("0r"):
                    year = year.replace("1r", "0r")

            found_people.append(ValidPersonDB(login=login, year=year, name=name, mail=mail))
            found_logins.append(login)

        for login in found_logins:
            if login not in old_logins:
                new_logins.append(login)

        await ctx.send(f"Našel jsem {len(new_logins)} nových loginů.")

        for person in found_people:
            session.merge(person)

        cnt_new = 0
        for person in session.query(ValidPersonDB):
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

    @cooldowns.default_cooldown
    @commands.check(room_check.is_in_modroom)
    @commands.command()
    async def get_db(self, ctx):
        process = subprocess.Popen(["ssh", "merlin"], stdout=subprocess.PIPE)
        try:
            output, error = process.communicate(timeout=15)
            if error:
                await ctx.send("Stažené databáze nějak nefunguje.")
                return
        except subprocess.TimeoutExpired:
            await ctx.send("Timeout při stahování databáze.")
            return
        with open("merlin-latest", "w") as f:
            f.write(output.decode("utf-8"))
        await ctx.send("Stažení databáze proběhlo úspěšně.")

    @cooldowns.default_cooldown
    @commands.check(room_check.is_in_modroom)
    @commands.command()
    async def get_users_login(self, ctx, member: disnake.Member):
        result = session.query(PermitDB).filter(PermitDB.discord_ID == str(member.id)).one_or_none()

        if result is None:
            await ctx.send("Uživatel není v databázi.")
            return

        person = session.query(ValidPersonDB).filter(ValidPersonDB.login == result.login).one_or_none()

        if person is None:
            await ctx.send(result.login)
            return

        await ctx.send(("Login: `{p.login}`\nJméno: `{p.name}`\n" "Ročník: `{p.year}`").format(p=person))

    @cooldowns.default_cooldown
    @commands.check(room_check.is_in_modroom)
    @commands.command()
    async def get_logins_user(self, ctx, login):
        result = session.query(PermitDB).filter(PermitDB.login == login).one_or_none()

        if result is None:
            person = session.query(ValidPersonDB).filter(ValidPersonDB.login == login).one_or_none()
            if person is None:
                await ctx.send("Uživatel není v databázi možných loginů.")
            else:
                await ctx.send(
                    ("Login: `{p.login}`\nJméno: `{p.name}`\n" "Ročník: `{p.year}`\nNení na serveru.").format(
                        p=person
                    )
                )
        else:
            await ctx.send(utils.generate_mention(result.discord_ID))

    @cooldowns.default_cooldown
    @commands.check(room_check.is_in_modroom)
    @commands.command()
    async def reset_login(self, ctx, login):

        result = session.query(ValidPersonDB).filter(ValidPersonDB.login == login).one_or_none()
        if result is None:
            await ctx.send("To není validní login.")
        else:
            session.query(PermitDB).filter(PermitDB.login == login).delete()
            result.status = 1
            session.commit()
            await ctx.send("Hotovo.")

    @cooldowns.default_cooldown
    @commands.check(room_check.is_in_modroom)
    @commands.command()
    async def connect_login_to_user(self, ctx, login, member: disnake.Member):

        result = session.query(ValidPersonDB).filter(ValidPersonDB.login == login).one_or_none()
        if result is None:
            await ctx.send("To není validní login.")
        else:
            session.add(PermitDB(login=login, discord_ID=str(member.id)))
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
    @connect_login_to_user.error
    async def fitwide_checks_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("Nothing to see here comrade. <:KKomrade:484470873001164817>")
            return True


def setup(bot):
    bot.add_cog(FitWide(bot))
