import asyncio
import shlex
from datetime import datetime, timedelta, timezone

import aiohttp
import disnake
from disnake.ext import commands

import utils
from config.app_config import config
from database.report import ReportDB
from database.timeout import TimeoutDB, TimeoutUserDB
from permissions.custom_errors import ApiError
from rubbergod import Rubbergod

from .messages_cz import MessagesCZ


def create_embed(
    author: disnake.User,
    title: str,
    description: str = None,
) -> disnake.Embed:
    """Embed template for Timeout"""
    embed = disnake.Embed(title=title, color=disnake.Color.yellow(), description=description)
    utils.general.add_author_footer(embed, author)
    return embed


def add_field_timeout(
    embed: disnake.Embed,
    title: str,
    member: disnake.User,
    author: disnake.User,
    starttime: datetime,
    endtime: datetime,
    length: timedelta,
    reason: str,
):
    author = f"{author.mention} (`{author.name}`)" if author else "Automod"

    embed.add_field(
        name=title,
        value=MessagesCZ.timeout_field_text(
            member=f"{member.mention} (`{member.name}`)",
            author=author,
            starttime=starttime.strftime("%d.%m.%Y %H:%M"),
            endtime=endtime.strftime("%d.%m.%Y %H:%M"),
            length=f"{length.days}d, " f"{length.seconds // 3600}h, " f"{(length.seconds // 60) % 60}m",
            timestamp=disnake.utils.format_dt(endtime, style="R"),
            reason=reason,
        ),
        inline=False,
    )


async def timeout_embed_listing(
    bot: Rubbergod,
    users: list[TimeoutDB],
    title: str,
    room: disnake.TextChannel,
    author: disnake.User,
) -> None:
    """Embed for sending timeout updates on users"""
    embeds = []
    users_lists = utils.general.split_to_parts(users, 15)  # to avoid embed char limit
    for users_list in users_lists:
        embed = create_embed(author, title)
        for timeout in users_list:
            mod = await bot.get_or_fetch_user(timeout.mod_id)
            starttime_local, endtime_local = timeout.start_end_local
            member = await bot.get_or_fetch_user(timeout.user_id)
            add_field_timeout(
                embed=embed,
                title=member.display_name,
                member=member,
                author=mod,
                starttime=starttime_local,
                endtime=endtime_local,
                length=timeout.length,
                reason=timeout.reason,
            )

        embeds.append(embed)
    await room.send(embeds=embeds)


async def timeout_perms(
    inter: disnake.ApplicationCommandInteraction,
    session: aiohttp.ClientSession,
    bot_dev_channel: disnake.TextChannel,
    member: disnake.Member,
    starttime: datetime | None,
    endtime: datetime | None,
    length: timedelta | None,
    reason: str,
    isself: bool = False,
    remove_logs: bool = False,
) -> bool:
    """Set timeout for member and update in db. Return True if successful, False otherwise."""
    mode = "delete" if remove_logs else "create"
    try:
        if endtime is None or length is None or starttime is None:
            await member.timeout(until=None, reason=reason)
            timeout = TimeoutDB.remove_timeout(member.id, remove_logs)
        elif length.days > 28:
            await member.timeout(until=datetime.now(timezone.utc) + timedelta(days=28), reason=reason)
            timeout = TimeoutDB.add_timeout(
                member.id,
                inter.author.id,
                starttime,
                endtime,
                reason,
                inter.guild.id,
                isself,
            )
        else:
            await member.timeout(until=endtime, reason=reason)
            timeout = TimeoutDB.add_timeout(
                member.id,
                inter.author.id,
                starttime,
                endtime,
                reason,
                inter.guild.id,
                isself,
            )

        if timeout:
            error = await send_to_grillbot(session, timeout, mode)
            if error:
                await bot_dev_channel.send(error)

        return True
    except disnake.Forbidden:
        # bot can't timeout member
        return False


async def parse_members(
    inter: disnake.ApplicationCommandInteraction, members_string: str
) -> list[disnake.Member] | None:
    """Parse members from string and return list of members"""

    member_string = shlex.split(members_string)
    converter = commands.MemberConverter()
    parsed_members = []
    not_found_members = []

    for member in member_string:
        try:
            parsed_members.append(await converter.convert(inter, member))
        except commands.MemberNotFound:
            not_found_members.append(member)

    if not_found_members:
        # print users that can't be found
        await inter.send(
            MessagesCZ.timeout_member_not_found(
                author=inter.author.mention, members=", ".join(not_found_members)
            ),
            ephemeral=True,
        )

    return parsed_members or None


async def timeout_get_user(
    author: disnake.User,
    guild_id: int,
    bot: Rubbergod,
    user: disnake.User,
) -> list[disnake.Embed]:
    timeout_user = TimeoutUserDB.get_user(user.id)
    if timeout_user:
        timeouts_count = timeout_user.timeout_count
        recent_timeout = timeout_user.get_last_timeout()
    else:
        timeouts_count = 0
        recent_timeout = None

    embeds = []
    main_embed = create_embed(
        author=author,
        title=f"`@{user.display_name}` timeouts",
        description=user.mention,
    )

    main_embed.add_field(name="Timeouts count", value=timeouts_count, inline=True)
    main_embed.add_field(name="Reports count", value=ReportDB.get_reports_on_user(user.id), inline=True)
    unverifies, warnings = await get_user_from_grillbot(bot.grillbot_session, guild_id, user.id)
    main_embed.add_field(
        name="Unverifies count",
        value=f"[{unverifies}](https://private.grillbot.eu/admin/unverify/logs)",
        inline=True,
    )
    main_embed.add_field(
        name="Warnings count",
        value=f"[{warnings}](https://private.grillbot.eu/admin/userMeasures)",
        inline=True,
    )

    if timeout_user and recent_timeout is not None:
        author = await bot.get_or_fetch_user(recent_timeout.mod_id)
        starttime_local, endtime_local = recent_timeout.start_end_local
        add_field_timeout(
            embed=main_embed,
            title="Recent timeout",
            member=user,
            author=author,
            starttime=starttime_local,
            endtime=endtime_local,
            length=recent_timeout.length,
            reason=recent_timeout.reason,
        )
        embeds.append(main_embed)

        embed = create_embed(author, f"`@{user.display_name}` timeouts")
        for index, timeout in enumerate(timeout_user.get_all_timeouts()):
            if (index % 5) == 0 and index != 0:
                embeds.append(embed)
                embed = create_embed(author, f"`@{user.display_name}` timeouts")

            author = await bot.get_or_fetch_user(timeout.mod_id)
            starttime_local, endtime_local = timeout.start_end_local
            add_field_timeout(
                embed=embed,
                title=user.display_name,
                member=user,
                author=author,
                starttime=starttime_local,
                endtime=endtime_local,
                length=timeout.length,
                reason=timeout.reason,
            )
        embeds.append(embed)
    else:
        embeds.append(main_embed)

    return embeds


async def get_user_from_grillbot(
    grillbot_session: aiohttp.ClientSession, guild_id: int, user_id: int
) -> tuple[int, int]:
    """Get unverify count and warning count"""
    try:
        url = f"{config.grillbot_api_url}/user/info/{guild_id}/{user_id}"
        async with grillbot_session.get(url) as resp:
            user = await resp.json()
            return user.get("unverifyCount", "Missing"), user.get("warningCount", "Missing")
    except (asyncio.exceptions.TimeoutError, aiohttp.client_exceptions.ClientConnectorError) as e:
        raise ApiError(str(e))


async def time_check(
    inter: disnake.ApplicationCommandInteraction, endtime: datetime | None, length: timedelta
) -> bool:
    if not endtime:
        await inter.send(MessagesCZ.invalid_time_format, ephemeral=True)
        return True

    if endtime < inter.created_at:
        await inter.send(MessagesCZ.past_time, ephemeral=True)
        return True

    if length.total_seconds() < 30:
        await inter.send(MessagesCZ.timeout_too_short, ephemeral=True)
        return True
    return False


async def send_to_grillbot(
    grillbot_session: aiohttp.ClientSession, timeout: TimeoutDB, mode: str = "create"
) -> str | None:
    """Send timeout data to grillbot api.

    Sending create/update timeout event or delete timeout event.
    """
    # if user got timeout from automod grillbot api expects user_id as mod_id
    if timeout.isself:
        return None

    mod_id = timeout.user_id if timeout.mod_id == "1" else timeout.mod_id
    if mode == "delete":
        try:
            url = f"{config.grillbot_api_url}/user/measures/timeout/{timeout.id}"
            async with grillbot_session.post(url) as response:
                if response.status != 200:
                    return MessagesCZ.error_msg(url=url, status=response.status, text=await response.text())
                return None
        except Exception as error:
            return str(error)

    try:
        url = f"{config.grillbot_api_url}/user/measures/timeout/create"
        data = {
            "timeoutId": f"{timeout.id}",
            "createdAtUtc": f"{timeout.start.replace(tzinfo=timezone.utc).isoformat()}",
            "moderatorId": f"{mod_id}",
            "targetUserId": f"{timeout.user_id}",
            "guildId": f"{timeout.guild_id}",
            "validToUtc": f"{timeout.end.replace(tzinfo=timezone.utc).isoformat()}",
            "reason": f"{timeout.reason}",
        }
        async with grillbot_session.post(url, json=data) as response:
            if response.status != 201:
                return MessagesCZ.error_msg(url=url, status=response.status, text=await response.text())
            return None
    except Exception as error:
        return str(error)
