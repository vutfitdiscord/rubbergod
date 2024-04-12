import disnake
from disnake.ext import commands

import utils
from config.app_config import config
from database.verification import ValidPersonDB

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
        message += utils.generate_mention(target_ids[index])
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
        progress_bar = utils.create_bar(index, len(categories))
        await message.edit(f"Přídávám práva pro roomky: {progress_bar}")
        for channel in category.channels:
            await channel.set_permissions(bit0, read_messages=True)
            await channel.set_permissions(mit0, read_messages=True)

    # skolni-info, cvicici-info, stream-links, senat-unie-drby room overwrites
    channel_names = ["skolni-info", "cvicici-info", "stream-links", "senat-unie-drby", "bp-szz", "dp-szz"]
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

    perms_list = None

    if channel_teachers:
        perms_list = f"**{channel.name.upper()}: {channel.mention}**\n"
        for teacher in channel_teachers:
            perms_list += f"- {teacher.mention} ({teacher.display_name})"
            user = ValidPersonDB.get_user_by_id(teacher.id)
            if user:
                perms_list += f" - {user.name}"
            perms_list += "\n"

    return perms_list


async def update_teacher_info(
    channel: disnake.abc.GuildChannel, teacher_info_channel: disnake.TextChannel
) -> tuple[str | None, str | None]:
    """Update teacher info channel"""
    teacher_roles = await get_teacher_roles(channel.guild)
    perms_list = await get_teacher_perms_list(channel, teacher_roles)

    if not perms_list:
        return None, None

    # Don't ping anyone
    no_one = disnake.AllowedMentions.none()

    async for message in teacher_info_channel.history():
        if message.author == channel.guild.me and channel.name.upper() in message.content:
            old_content = message.content
            await message.edit(content=perms_list, allowed_mentions=no_one)
            return old_content, perms_list
        elif channel.name.upper() in message.content:
            old_content = message.content
            await message.delete()
            await teacher_info_channel.send(perms_list, allowed_mentions=no_one)
            return old_content, perms_list

    # Channel had no listing yet
    await teacher_info_channel.send(perms_list, allowed_mentions=no_one)
    return None, perms_list
