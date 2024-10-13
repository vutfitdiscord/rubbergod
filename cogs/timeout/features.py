import asyncio
from datetime import datetime, timedelta, timezone

import aiohttp
import disnake

import utils
from config.app_config import config
from database.report import ReportDB
from database.timeout import TimeoutDB, TimeoutUserDB
from permissions.custom_errors import ApiError, InvalidTime
from rubbergod import Rubbergod

from .messages_cz import MessagesCZ

TIMESTAMPS = [
    "60s",
    "5min",
    "10min",
    "1hour",
    "4hours",
    "8hours",
    "12hours",
    "16hours",
    "1day",
    "3days",
    "1week",
    "2weeks",
    "3weeks",
    "4weeks",
    "Forever",
]


def create_embed(
    author: disnake.User,
    title: str,
    description: str = None,
) -> disnake.Embed:
    """Embed template for Timeout"""
    embed = disnake.Embed(title=title, color=disnake.Color.yellow(), description=description)
    utils.embed.add_author_footer(embed, author)
    return embed


async def add_field_timeout(
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
    bot: Rubbergod, users: list[TimeoutDB], author: disnake.User
) -> list[disnake.Embed]:
    """Embed for sending timeout updates on users"""
    embeds = []
    users_lists = utils.general.split_to_parts(users, 10)
    for users_list in users_lists:
        embed = create_embed(author, "Timeout list")
        for timeout in users_list:
            mod = await bot.get_or_fetch_user(timeout.mod_id)
            starttime_local, endtime_local = timeout.start_end_local
            member = await bot.get_or_fetch_user(timeout.user_id)
            await add_field_timeout(
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
    return embeds


async def embed_update_list(counts: dict[str, int], author: disnake.User) -> disnake.Embed:
    """Embed for sending timeout updates on users"""
    embed = create_embed(author, "Timeout update")

    embed.add_field(name="Timeouts", value=counts["timeouts"], inline=True)
    embed.add_field(name="Infinite Timeouts", value=counts["infinite timeouts"], inline=True)
    embed.add_field(name="Selftimeouts", value=counts["selftimeouts"], inline=True)
    embed.add_field(name="Sum of timeouts", value=counts["sum"], inline=False)

    return embed


async def set_timeout_db(
    inter: disnake.ApplicationCommandInteraction,
    grillbot_session: aiohttp.ClientSession,
    bot_dev_channel: disnake.TextChannel,
    user: disnake.Member,
    starttime: datetime | None,
    endtime: datetime | None,
    reason: str,
    isself: bool = False,
    remove_logs: bool = False,
) -> None:
    """Set timeout for user in database."""
    if not starttime or not endtime:
        # remove timeout
        timeout = TimeoutDB.remove_timeout(user.id, remove_logs)
    else:
        # set timeout
        timeout = TimeoutDB.add_timeout(
            user_id=user.id,
            mod_id=inter.author.id,
            start=starttime,
            end=endtime,
            reason=reason,
            guild_id=inter.guild.id,
            isself=isself,
        )

    if timeout:
        # send timeout to grillbot api
        mode = "delete" if remove_logs else "create"
        error = await send_to_grillbot(grillbot_session, timeout, mode)
        if error:
            await bot_dev_channel.send(error)


async def set_member_timeout(
    member: disnake.Member,
    starttime: datetime | None,
    endtime: datetime | None,
    reason: str,
) -> None:
    """Set timeout for member. Return True if successful, False otherwise."""
    if not starttime or not endtime:
        # remove timeout
        await member.timeout(until=None, reason=reason)
    elif (endtime - starttime).days > 28:
        # timeout longer than discord supports, setting it to max 28 days
        await member.timeout(until=datetime.now(timezone.utc) + timedelta(days=28), reason=reason)
    else:
        # normal timeout in range <60s, 28days>
        await member.timeout(until=endtime, reason=reason)


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
        await add_field_timeout(
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
            await add_field_timeout(
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


async def time_check(created_at: datetime, endtime: datetime) -> None:
    """Check if timeout time is valid. Raise `InvalidTime` if not."""
    if endtime < created_at:
        raise InvalidTime(MessagesCZ.past_time)

    length = endtime - created_at
    if length.total_seconds() < 60:
        raise InvalidTime(MessagesCZ.timeout_too_short)


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
            async with grillbot_session.delete(url) as response:
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


async def autocomplete_times(inter: disnake.ApplicationCommandInteraction, input: str) -> list[str]:
    input = input.lower()
    return [endtime for endtime in TIMESTAMPS if input in endtime.lower()]
