"""
Cog implementing management of year roles and database of user logins.
"""

import asyncio
import json
from datetime import datetime, timezone
from io import BytesIO

import disnake
from disnake.ext import commands

import utils
from cogs.base import Base
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
    @commands.slash_command(name="verify_check", description=MessagesCZ.verify_check_brief)
    async def verify_check(self, inter: disnake.ApplicationCommandInteraction):
        await inter.send(MessagesCZ.role_check_start)
        message = await inter.original_response()
        guild = inter.guild
        verified = await features.get_verified_members(guild)

        permitted = PermitDB.get_all_users()
        permitted_ids = [int(person.discord_ID) for person in permitted]

        for member in verified:
            if member.id not in permitted_ids:
                await message.reply(MessagesCZ.verify_check_user_not_found(user=member.id, id=member.id))

        await message.reply(MessagesCZ.role_check_end)

    @cooldowns.default_cooldown
    @commands.check(permission_check.is_bot_admin)
    @commands.check(room_check.is_in_modroom)
    @commands.slash_command(name="status_check", description=MessagesCZ.status_check_brief)
    async def status_check(self, inter: disnake.ApplicationCommandInteraction):
        await inter.send(MessagesCZ.role_check_start)
        message = await inter.original_response()
        guild = inter.guild
        verified = await features.get_verified_members(guild)

        for member in verified:
            users = PermitDB.get_all_users_by_id(member.id)
            if not users:
                continue
            if len(users) > 1:
                await message.reply(MessagesCZ.status_check_user_duplicate(user=member.id, id=member.id))
                continue

            user = users[0]

            person = ValidPersonDB.get_user_by_login(user.login)
            if person is None:
                continue

            if person.status != VerifyStatus.Verified.value:
                await message.reply(
                    MessagesCZ.status_check_wrong_status(user=user.discord_ID, id=user.discord_ID)
                )

        await message.reply(MessagesCZ.role_check_end)

    @cooldowns.default_cooldown
    @commands.check(permission_check.is_bot_admin)
    @commands.check(room_check.is_in_modroom)
    @commands.slash_command(name="zapis_check", description=MessagesCZ.zapis_check_brief)
    async def zapis_check(self, inter: disnake.ApplicationCommandInteraction):
        await inter.send(MessagesCZ.role_check_start)
        message = await inter.original_response()
        guild = inter.guild

        unmatching_members = await features.get_members_with_unmatching_year(guild)

        for source_role, target_data in unmatching_members.items():
            for target_role, target_members in target_data.items():
                if len(target_members) == 0:
                    continue
                source_year = source_role.name
                target_year = target_role.name
                target_ids = [member.id for member in target_members]
                if (
                    ("BIT" in source_year and "BIT" in target_year)
                    or ("MIT" in source_year and "MIT" in target_year)
                ) and int(source_year[0]) == int(target_year[0]) + 1:
                    await message.reply(MessagesCZ.zapis_check_found(target_year=target_year))
                    await features.send_masstag_messages(inter, "", target_ids)

        await message.reply(MessagesCZ.role_check_end)

    @cooldowns.default_cooldown
    @commands.check(permission_check.is_bot_admin)
    @commands.check(room_check.is_in_modroom)
    @commands.slash_command(name="mit_check", description=MessagesCZ.mit_check_brief)
    async def mit_check(self, inter: disnake.ApplicationCommandInteraction, p_debug: bool = True):
        await inter.send(MessagesCZ.role_check_start)
        message = await inter.original_response()
        guild = inter.guild

        unmatching_members = await features.get_members_with_unmatching_year(guild)

        for source_role, target_data in unmatching_members.items():
            for target_role, target_members in target_data.items():
                if len(target_members) == 0:
                    continue
                source_year = source_role.name
                target_year = target_role.name
                target_ids = [member.id for member in target_members]
                if (
                    # presun bakalaru do 1MIT
                    "BIT" in source_year and target_year == "1MIT"
                ):
                    await message.reply(
                        MessagesCZ.role_check_move(
                            people_count=len(target_members), target_year=target_year, source_year=source_year
                        )
                    )
                    await features.send_masstag_messages(inter, "", target_ids)
                    if p_debug:
                        await message.reply(MessagesCZ.role_check_debug_mode)
                        continue

                    for member in target_members:
                        await member.add_roles(target_role)
                        await member.remove_roles(source_role)

        await message.reply(MessagesCZ.role_check_end)

    @cooldowns.default_cooldown
    @commands.check(permission_check.is_bot_admin)
    @commands.check(room_check.is_in_modroom)
    @commands.slash_command(name="dropout_check", description=MessagesCZ.dropout_check_brief)
    async def dropout_check(self, inter: disnake.ApplicationCommandInteraction, p_debug: bool = True):
        await inter.send(MessagesCZ.role_check_start)
        message = await inter.original_response()
        guild = inter.guild

        survivor = disnake.utils.get(guild.roles, name="Survivor")
        king = disnake.utils.get(guild.roles, name="King")

        dropout_alternatives = [survivor, king]

        unmatching_members = await features.get_members_with_unmatching_year(guild)

        for source_role, target_data in unmatching_members.items():
            for target_role, target_members in target_data.items():
                if len(target_members) == 0:
                    continue
                source_year = source_role.name
                target_year = target_role.name
                target_ids = [member.id for member in target_members]
                if target_year == "Dropout":
                    await message.reply(
                        MessagesCZ.role_check_move(
                            people_count=len(target_members), target_year=target_year, source_year=source_year
                        )
                    )
                    await features.send_masstag_messages(inter, "", target_ids)
                    if p_debug:
                        await message.reply(MessagesCZ.role_check_debug_mode)
                        continue

                    for member in target_members:
                        if not (any(role in member.roles for role in dropout_alternatives)):
                            await member.add_roles(target_role)
                        await member.remove_roles(source_role)

        await message.reply(MessagesCZ.role_check_end)

    @cooldowns.default_cooldown
    @commands.check(permission_check.is_bot_admin)
    @commands.check(room_check.is_in_modroom)
    @commands.slash_command(name="role_check", description=MessagesCZ.role_check_brief)
    async def role_check(self, inter: disnake.ApplicationCommandInteraction):
        await inter.send(MessagesCZ.role_check_start)
        message = await inter.original_response()
        guild = inter.guild

        unmatching_members = await features.get_members_with_unmatching_year(guild)

        for source_role, target_data in unmatching_members.items():
            for target_role, target_members in target_data.items():
                if len(target_members) == 0:
                    continue
                source_year = source_role.name
                target_year = target_role.name
                target_ids = [member.id for member in target_members]

                await message.reply(
                    MessagesCZ.role_check_found(
                        people_count=len(target_members), target_year=target_year, source_year=source_year
                    )
                )
                await features.send_masstag_messages(inter, "", target_ids)

        await message.reply(MessagesCZ.role_check_end)

    @cooldowns.default_cooldown
    @commands.check(permission_check.is_bot_admin)
    @commands.slash_command(name="increment_roles", description=MessagesCZ.increment_roles_brief)
    async def increment_roles(self, inter: disnake.ApplicationCommandInteraction):
        await inter.send(MessagesCZ.increment_roles_start)
        message = await inter.original_response()
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
        self,
        inter: disnake.ApplicationCommandInteraction,
        continue_from_login: str = commands.Param(
            default="",
            autocomplete=autocomp_user_logins,
            description=MessagesCZ.update_db_continue_from_login,
        ),
    ):
        await inter.send(MessagesCZ.update_db_start)
        message = await inter.original_response()

        all_persons = ValidPersonDB.get_all_persons()
        persons_count = len(all_persons)
        dropout_count = 0

        if continue_from_login:
            for index, person in enumerate(all_persons):
                if person.login == continue_from_login:
                    all_persons = all_persons[index:]
                    break

        for index, person in enumerate(all_persons):
            if (index % 50) == 0:
                progress_bar = utils.general.create_bar(index, persons_count)
                await message.edit(MessagesCZ.update_db_progress(progress_bar=progress_bar))

            if (index % 10) == 0:
                # The simplest solution we could think of so that we don't hit rate limit
                await asyncio.sleep(60)

            self.bot.logger.info(f"Checking {person.login}")
            updated_person = await self.helper.check_api(person.login)
            if updated_person is None:
                if person.year != "MUNI" and person.year != "dropout":
                    person.year = "dropout"
                    dropout_count += 1
                continue

            # This will have the side-effect of mixing up "0bit"/"0mit" with the others again
            # until the enrollment to the next year
            ValidPersonDB.merge_person(updated_person)

        await message.reply(MessagesCZ.update_db_done(dropout_count=dropout_count))

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
    @zapis_check.error
    @status_check.error
    @dropout_check.error
    @mit_check.error
    @verify_check.error
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
