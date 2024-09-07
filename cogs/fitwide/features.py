import disnake
from disnake.ext import commands

import utils
from config.app_config import config
from database.verification import PermitDB, ValidPersonDB
from features.verification import Verification

CATEGORIES_NAMES = [
    "1. semestr", "2. semestr", "3. semestr", "4. semestr", "5. semestr",
    "zimni-volitelne", "letni-volitelne", "volitelne",
    "zimni magistersky semestr 1", "letni magistersky semestr 1",
    "zimni magistersky semestr 2", "letni magistersky semestr 2",
]  # fmt: skip


async def send_masstag_messages(ctx: commands.Context, prefix: str, target_ids: list[int]) -> None:
    message = prefix
    for index in range(len(target_ids)):
        # 35 sounds like a safe amount of tags per message
        if index % 35 == 0 and index:
            await ctx.send(message)
            message = prefix
        message += utils.user.generate_mention(target_ids[index])
        message += " "
    await ctx.send(message)


async def set_channel_permissions_for_new_students(
    message: disnake.Message,
    guild: disnake.Guild,
    bit0: disnake.Role,
    mit0: disnake.Role,
    bit_terminy_channels: list,
    info_channels: list,
) -> None:
    """Set permissions for new 0bit and 0mit roles to see school channels"""
    # Get all semester categories
    categories = [
        disnake.utils.get(guild.categories, name=semester_name) for semester_name in CATEGORIES_NAMES
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
        progress_bar = utils.general.create_bar(index, len(categories))
        await message.edit(f"Přídávám práva pro roomky: {progress_bar}")
        for channel in category.channels:
            await channel.set_permissions(bit0, read_messages=True)
            await channel.set_permissions(mit0, read_messages=True)

    # skolni-info, cvicici-info, stream-links, senat-unie-drby room overwrites
    channel_names = ["skolni-info", "vyucujici-info", "stream-links", "senat-unie-drby", "bp-szz", "dp-szz"]
    channels = [disnake.utils.get(guild.channels, name=channel_name) for channel_name in channel_names]
    for channel in channels:
        await channel.set_permissions(bit0, read_messages=True)
        await channel.set_permissions(mit0, read_messages=True)


async def get_teacher_roles(guild: disnake.Guild) -> list[disnake.Role]:
    return [disnake.utils.get(guild.roles, id=role_id) for role_id in config.teacher_roles]


async def get_teacher_perms_list(
    channel: disnake.abc.GuildChannel, teacher_roles: list[disnake.Role]
) -> str | None:
    """Get message with teacher permissions"""
    channel_teachers = []
    for user, permission in channel.overwrites.items():
        if not isinstance(user, disnake.Member):  # Only user overwrites
            continue

        # Check if user is a teacher
        if not set(user.roles).intersection(teacher_roles):
            continue

        # Check if user has permission to read messages
        if not permission.read_messages:
            continue

        channel_teachers.append(user)

    channel_teachers.sort()
    perms_list = None

    if channel_teachers:
        perms_list = f"**===== {channel.name.upper()}: {channel.mention} =====**\n"
        for teacher in channel_teachers:
            perms_list += f"- {teacher.mention} ({teacher.display_name})"
            user = ValidPersonDB.get_user_by_id(teacher.id)
            if user:
                # Get Full Name in reverse order
                last_name, first_name = user.name.split(" ")
                if first_name and last_name:
                    perms_list += f" - {first_name} {last_name}"
            perms_list += "\n"

    return perms_list


async def send_teacher_info(perms_list: str | None, teacher_info_channel: disnake.TextChannel) -> None:
    """
    Send teacher permissions message to teacher_info_channel, don't ping but send user data
    The library does not send user data on disabled mentions, so we have to edit the mention and send them manually afterwards
    See: https://github.com/discord/discord-api-docs/issues/2126
    """
    if perms_list:
        message = await teacher_info_channel.send("Generating...")
        await message.edit(content=perms_list)


async def update_teacher_info(
    channel: disnake.abc.GuildChannel, teacher_info_channel: disnake.TextChannel
) -> tuple[str | None, str | None]:
    """Update teacher info channel"""
    teacher_roles = await get_teacher_roles(channel.guild)
    new_perms_list = await get_teacher_perms_list(channel, teacher_roles)

    async for message in teacher_info_channel.history():
        if channel.name.upper() in message.content:
            old_perms_list = message.content
            if new_perms_list:
                if message.author == channel.guild.me:  # Can edit only my own messages
                    await message.edit(content=new_perms_list)
                else:  # If not mine, delete and resend
                    await message.delete()
                    await send_teacher_info(new_perms_list, teacher_info_channel)
            else:  # Channel had listing but now it's empty
                await message.delete()
            return old_perms_list, new_perms_list

    # Channel had no listing yet
    await send_teacher_info(new_perms_list, teacher_info_channel)
    return None, new_perms_list


async def get_verified_members(guild: disnake.Guild) -> list[disnake.Member]:
    members = guild.members

    verify = disnake.utils.get(guild.roles, name="Verify")
    host = disnake.utils.get(guild.roles, name="Host")
    bot = disnake.utils.get(guild.roles, name="Bot")
    poradce = disnake.utils.get(guild.roles, name="Poradce")
    vut = disnake.utils.get(guild.roles, name="VUT")

    verified = [
        member
        for member in members
        if verify in member.roles
        and host not in member.roles
        and bot not in member.roles
        and poradce not in member.roles
        and vut not in member.roles
    ]

    return verified


async def get_members_with_unmatching_year(
    guild: disnake.Guild,
) -> dict[disnake.Role, dict[disnake.Role, list[disnake.Member]]]:
    verified = await get_verified_members(guild)

    dropout = disnake.utils.get(guild.roles, name="Dropout")
    survivor = disnake.utils.get(guild.roles, name="Survivor")
    king = disnake.utils.get(guild.roles, name="King")

    dropout_alternatives = [survivor, king]

    years = ["0BIT", "1BIT", "2BIT", "3BIT+", "0MIT", "1MIT", "2MIT+", "Doktorand", "VUT", "Dropout"]

    year_roles = {year: disnake.utils.get(guild.roles, name=year) for year in years}

    unmatching_members: dict[disnake.Role, dict[disnake.Role, list[disnake.Member]]] = {
        year_y: {year_x: [] for year_x in year_roles.values()} for year_y in year_roles.values()
    }

    # collects all members whose database "year" doesn't match their role
    # the first dictionary key is the role they have currently
    # while the value is another dictionary with keys of the role they should have
    for member in verified:
        user = PermitDB.get_user_by_id(member.id)
        if user is None:
            continue

        person = ValidPersonDB.get_user_by_login(user.login)
        if person is None:
            continue

        year = Verification.transform_year(person.year)

        if year is None:
            year = "Dropout"

        correct_role = disnake.utils.get(guild.roles, name=year)

        if correct_role not in member.roles:
            for role in year_roles.values():
                if role in member.roles and correct_role in unmatching_members[role].keys():
                    unmatching_members[role][correct_role].append(member)
                    break
                elif not (
                    correct_role == dropout and any(role in member.roles for role in dropout_alternatives)
                ):
                    unmatching_members[dropout][correct_role].append(member)

    return unmatching_members
