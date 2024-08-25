"""
Cog implementing management of year roles and database of user logins.
"""

import json
import subprocess
from datetime import datetime, timezone
from io import BytesIO

import disnake
from disnake.ext import commands

import utils
from cogs.base import Base
from database import session
from database.verification import PermitDB, ValidPersonDB, VerifyStatus
from features.verification import Verification
from features.verify_helper import VerifyHelper
from permissions import permission_check, room_check
from rubbergod import Rubbergod
from utils import cooldowns

from . import features
from .messages_cz import MessagesCZ

user_logins: list[str] = []


async def autocomp_user_logins(inter: disnake.ApplicationCommandInteraction, user_input: str):
    return [user for user in user_logins if user_input.lower() in user][:25]


class FitWide(Base, commands.Cog):
    def __init__(self, bot: Rubbergod):
        super().__init__()
        self.bot = bot
        self.verification = Verification(bot)
        self.helper = VerifyHelper(bot)
        self.get_all_logins()

    def get_all_logins(self):
        global user_logins
        user_logins_verified = PermitDB.get_all_logins()
        user_logins_not_verified = ValidPersonDB.get_all_logins()
        verified_logins = [user[0] for user in user_logins_verified]
        not_verified_logins = [user[0] for user in user_logins_not_verified]
        user_logins = set(verified_logins + not_verified_logins)
        user_logins = sorted(user_logins)

    @cooldowns.default_cooldown
    @commands.check(permission_check.is_bot_admin)
    @commands.check(room_check.is_in_modroom)
    @commands.slash_command(name="role_check", description=MessagesCZ.role_check_brief)
    async def role_check(
        self,
        inter: disnake.ApplicationCommandInteraction,
        p_verified: bool = True,
        p_move: bool = False,
        p_status: bool = True,
        p_role: bool = True,
        p_zapis: bool = False,
        p_debug: bool = True,
    ):
        await inter.send(MessagesCZ.role_check_start)
        guild = inter.guild
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

        permitted = session.query(PermitDB)
        permitted_ids = [int(person.discord_ID) for person in permitted]

        years = ["0BIT", "1BIT", "2BIT", "3BIT+", "0MIT", "1MIT", "2MIT+", "Doktorand", "VUT", "Dropout"]

        year_roles = {year: disnake.utils.get(guild.roles, name=year) for year in years}

        weird_members: dict[disnake.Role, dict[disnake.Role, list[disnake.Member]]] = {
            year_y: {year_x: [] for year_x in year_roles.values()} for year_y in year_roles.values()
        }

        for member in verified:
            if member.id not in permitted_ids:
                if p_verified:
                    await inter.send(MessagesCZ.role_check_user_not_found(user=member.id, id=member.id))
            else:
                user = PermitDB.get_user_by_id(member.id)
                if user is None:
                    continue
                if len(user) > 1:
                    await inter.send(MessagesCZ.role_check_user_duplicate(user=member.id, id=member.id))
                    continue

                person = ValidPersonDB.get_user_by_login(user.login)
                if person is None:
                    continue

                if person.status != 0:
                    if p_status:
                        await inter.send(
                            MessagesCZ.role_check_wrong_status(user=user.discord_ID, id=user.discord_ID)
                        )

                year = self.verification.transform_year(person.year)

                if year is None:
                    year = "Dropout"

                correct_role = disnake.utils.get(guild.roles, name=year)

                if correct_role not in member.roles:
                    for role in year_roles.values():
                        if role in member.roles and correct_role in weird_members[role].keys():
                            weird_members[role][correct_role].append(member)
                            break
                    else:
                        if not (
                            correct_role == dropout
                            and any(role in member.roles for role in dropout_alternatives)
                        ):
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
                        "Vypadá, že do dalšího ročníku se nezapsali "
                        f"(protoze na merlinovi maji {target_year}): "
                    )
                    await features.send_masstag_messages(inter, message_prefix, target_ids)
                elif p_move and (
                    # presun bakalaru do 1MIT
                    ("BIT" in source_year and target_year == "1MIT") or target_year == "Dropout"
                ):
                    await inter.send(
                        f"Přesouvám tyto {len(target_members)} lidi z {source_year} do {target_year}:"
                    )
                    await features.send_masstag_messages(inter, "", target_ids)
                    if p_debug:
                        await inter.send("jk, debug mode")
                    else:
                        for member in target_members:
                            if not (
                                target_role == dropout
                                and any(role in member.roles for role in dropout_alternatives)
                            ):
                                await member.add_roles(target_role)
                            await member.remove_roles(source_role)
                elif p_role:
                    await inter.send(
                        f"Našel jsem {len(target_members)} lidi, kteří mají na merlinovi "
                        f"{target_year} ale roli {source_year}:"
                    )
                    await features.send_masstag_messages(inter, "", target_ids)

        await inter.send("Done")

    @cooldowns.default_cooldown
    @commands.check(permission_check.is_bot_admin)
    @commands.slash_command(name="increment_roles", description=MessagesCZ.increment_roles_brief)
    async def increment_roles(self, inter: disnake.ApplicationCommandInteraction):
        await inter.send(MessagesCZ.increment_roles_start)
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
                progress_bar = utils.general.create_bar(index, len(bit4_members))
                await message.edit(f"Přidávání role 4bit-1mit: {progress_bar}")

        # give 3bit/2mit users 2bit/1mit role
        for index, member in enumerate(BIT_roles[3].members):
            await member.add_roles(BIT_roles[2])
            if (index % 50) == 0:
                progress_bar = utils.general.create_bar(index, len(BIT_roles[3].members))
                await message.edit(f"Přidávání role 3bit: {progress_bar}")

        for index, member in enumerate(MIT_roles[2].members):
            if (index % 50) == 0:
                progress_bar = utils.general.create_bar(index, len(MIT_roles[2].members))
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
        await message.edit(MessagesCZ.increment_roles_names)

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
            bit4: disnake.PermissionOverwrite(read_messages=True, send_messages=True),
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
        await message.edit(MessagesCZ.increment_roles_room_names)

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
                create_public_threads=False,
            ),
            disnake.utils.get(guild.roles, name="1BIT"): disnake.PermissionOverwrite(read_messages=True),
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

        await features.set_channel_permissions_for_new_students(
            message, guild, BIT_roles[0], MIT_roles[0], bit_terminy_channels, info_channels
        )

        await inter.edit_original_response(MessagesCZ.increment_roles_success)

    @cooldowns.default_cooldown
    @commands.check(room_check.is_in_modroom)
    @commands.slash_command(name="verify_db", description=MessagesCZ.fitwide_brief)
    async def verify_db(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @verify_db.sub_command(name="update", description=MessagesCZ.update_db_brief)
    async def update_db(
        self, inter: disnake.ApplicationCommandInteraction, convert_to_0bit_0mit: bool = False
    ):
        await inter.send(MessagesCZ.update_db_start)
        with open("merlin-latest", "r") as f:
            data = f.readlines()

        found_people = []
        found_logins = []
        new_logins = []
        login_results = ValidPersonDB.get_all_logins()
        # Use unpacking on results
        old_logins = [value for (value,) in login_results]

        for line in data:
            line_split = line.split(":")
            login = line_split[0]
            name = line_split[4].split(",", 1)[0]
            try:
                year_fields = line_split[4].split(",")[1].split(" ")
                year = " ".join(year_fields if "mail=" not in year_fields[-1] else year_fields[:-1])
                mail = year_fields[-1].replace("mail=", "") if "mail=" in year_fields[-1] else None
            except IndexError:
                continue

            if convert_to_0bit_0mit and year.endswith("1r"):
                person = ValidPersonDB.get_user_by_login(login)
                if person is not None and person.year.endswith("0r"):
                    year = year.replace("1r", "0r")

            found_people.append(ValidPersonDB(login=login, year=year, name=name, mail=mail))
            found_logins.append(login)

        for login in found_logins:
            if login not in old_logins:
                new_logins.append(login)

        await inter.send(MessagesCZ.new_logins(new_logins=len(new_logins)))

        for person in found_people:
            session.merge(person)

        cnt_new = 0
        all_persons = ValidPersonDB.get_all_persons()
        for person in all_persons:
            if person.login not in found_logins:
                try:
                    # check for muni
                    int(person.login)
                    person.year = "MUNI"
                except ValueError:
                    person.year = "dropout"
            elif convert_to_0bit_0mit and person.login in new_logins:
                if person.year.endswith("1r"):
                    person.year = person.year.replace("1r", "0r")
                    cnt_new += 1

        session.commit()

        await inter.send(MessagesCZ.update_db_done)
        if convert_to_0bit_0mit:
            await inter.send(MessagesCZ.db_debug(cnt_new=cnt_new))

    @verify_db.sub_command(name="pull", description=MessagesCZ.pull_db_brief)
    async def pull_db(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        process = subprocess.Popen(
            ["ssh", "-i", self.config.db_pull_merlin_key_path, "merlin"], stdout=subprocess.PIPE
        )
        try:
            output, error = process.communicate(timeout=15)
            if error:
                await inter.edit_original_response(MessagesCZ.get_db_error)
                return
        except subprocess.TimeoutExpired:
            await inter.edit_original_response(MessagesCZ.get_db_timeout)
            return
        with open("merlin-latest", "w") as f:
            f.write(output.decode("utf-8"))
        await inter.edit_original_response(MessagesCZ.get_db_success)

    @verify_db.sub_command(name="get_login", description=MessagesCZ.get_login_brief)
    async def get_login(self, inter: disnake.ApplicationCommandInteraction, member: disnake.User):
        await inter.response.defer()
        result = PermitDB.get_user_by_id(member.id)

        if result is None:
            await inter.edit_original_response(MessagesCZ.login_not_found)
            return

        person = ValidPersonDB.get_user_by_login(result.login)

        if person is None:
            await inter.edit_original_response(result.login)
            return

        await inter.edit_original_response(MessagesCZ.get_user_format(p=person))

    @verify_db.sub_command(name="get_user", description=MessagesCZ.get_user_brief)
    async def get_user(
        self,
        inter: disnake.ApplicationCommandInteraction,
        login: str = commands.Param(autocomplete=autocomp_user_logins),
    ):
        await inter.response.defer()
        result = PermitDB.get_user_by_login(login)

        if result is None:
            person = ValidPersonDB.get_user_by_login(login)
            if person is None:
                await inter.edit_original_response(MessagesCZ.get_user_not_found)
            else:
                await inter.edit_original_response(MessagesCZ.get_user_format(p=person) + "Není na serveru.")
        else:
            await inter.edit_original_response(utils.user.generate_mention(result.discord_ID))

    @verify_db.sub_command(name="reset_login", description=MessagesCZ.reset_login_brief)
    async def reset_login(
        self,
        inter: disnake.ApplicationCommandInteraction,
        login: str = commands.Param(autocomplete=autocomp_user_logins),
    ):
        await inter.response.defer()
        result = ValidPersonDB.get_user_by_login(login)

        if result is None:
            await inter.edit_original_response(MessagesCZ.invalid_login)
        else:
            try:
                PermitDB.delete_user_by_login(login)
            except Exception:
                await inter.edit_original_response(MessagesCZ.login_not_found)
                return
            result.change_status(VerifyStatus.Unverified.value)
            await inter.edit_original_response(MessagesCZ.action_success)

    @verify_db.sub_command(name="link_login_user", description=MessagesCZ.link_login_user_brief)
    async def link_login_user(
        self,
        inter: disnake.ApplicationCommandInteraction,
        member: disnake.Member,
        login: str = commands.Param(autocomplete=autocomp_user_logins),
    ):
        await inter.response.defer()
        result = ValidPersonDB.get_user_by_login(login)
        if result is None:
            await inter.edit_original_response(MessagesCZ.invalid_login)
        else:
            try:
                PermitDB.add_user(login, str(member.id))
            except Exception:
                await inter.edit_original_response(MessagesCZ.login_already_exists)
                return
            result.change_status(VerifyStatus.Verified.value)
            await inter.edit_original_response(MessagesCZ.action_success)

    @cooldowns.default_cooldown
    @commands.check(room_check.is_in_modroom)
    @commands.slash_command(name="vutapi", description=MessagesCZ.vutapi_brief)
    async def vutapi(
        self,
        inter: disnake.ApplicationCommandInteraction,
        login: str = commands.Param(autocomplete=autocomp_user_logins),
    ):
        await inter.response.defer()
        res = await self.helper.get_user_details(login)
        with BytesIO(bytes(json.dumps(res, indent=2, ensure_ascii=False), "utf-8")) as file:
            file = disnake.File(fp=file, filename=f"{login}.json")
            await inter.edit_original_response(file=file)

    @verify_db.error
    @role_check.error
    async def fitwide_checks_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.CheckFailure):
            await inter.send(MessagesCZ.not_in_modroom)
            return True

    @cooldowns.default_cooldown
    @commands.check(room_check.is_in_modroom)
    @commands.slash_command(name="gen_teacher_info", description=MessagesCZ.gen_teacher_info_brief)
    async def gen_teacher_info(self, inter: disnake.ApplicationCommandInteraction):
        """Generate teacher info channel"""
        await inter.send(MessagesCZ.gen_teacher_info_start)
        # Get all semester categories
        categories = [
            disnake.utils.get(inter.guild.categories, name=semester_name)
            for semester_name in features.CATEGORIES_NAMES
        ]

        # Check if all categories were found
        invalid_categories = [
            semester_name
            for semester_name, category in zip(features.CATEGORIES_NAMES, categories)
            if category is None
        ]
        if invalid_categories:
            # Tell which categories were invalid
            await inter.edit_original_response(
                MessagesCZ.gen_teacher_info_inv_catg(categories=invalid_categories)
            )
            return

        teacher_roles = await features.get_teacher_roles(inter.guild)

        if None in teacher_roles:
            await inter.edit_original_response(MessagesCZ.gen_teacher_info_inv_roles)
            return

        if self.teacher_info_channel is None:
            await inter.edit_original_response(MessagesCZ.gen_teacher_info_channel_none)
            return

        # Clear channel before sending new data
        await self.teacher_info_channel.purge(limit=None)
        await self.teacher_info_channel.send(MessagesCZ.gen_teacher_info_header)

        # Run through all semester channels
        for index, category in enumerate(categories):
            progress_bar = utils.general.create_bar(index, len(categories))
            await inter.edit_original_message(
                content=MessagesCZ.gen_teacher_info_processing(progress_bar=progress_bar)
            )
            for channel in category.channels:
                perms_list = await features.get_teacher_perms_list(channel, teacher_roles)
                if perms_list:
                    await features.send_teacher_info(perms_list, self.teacher_info_channel)

        await inter.edit_original_response(MessagesCZ.gen_teacher_info_success)

    @commands.Cog.listener()
    async def on_guild_channel_update(
        self, before: disnake.abc.GuildChannel, after: disnake.abc.GuildChannel
    ) -> None:
        """Update teacher info channel on permissions change"""
        if before.overwrites != after.overwrites and after.category.name in features.CATEGORIES_NAMES:
            perms_list_before, perms_list_after = await features.update_teacher_info(
                after, self.teacher_info_channel
            )
            if perms_list_before == perms_list_after:
                return
            embed = disnake.Embed(title="Teacher permissions update", color=disnake.Colour.yellow())
            missing = "None"
            embed.description = f"## Old permissions\n{perms_list_before or missing}\n## New permissions\n{perms_list_after or missing}"
            embed.timestamp = datetime.now(tz=timezone.utc)
            await self.log_channel.send(embed=embed, allowed_mentions=disnake.AllowedMentions.none())
