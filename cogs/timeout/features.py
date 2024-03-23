import asyncio
import shlex
from datetime import datetime, timedelta, timezone

import aiohttp
import disnake
from disnake.ext import commands

import utils
from config.app_config import config
from database.timeout import TimeoutDB
from permissions.custom_errors import ApiError

from .messages_cz import MessagesCZ


def create_embed(
    author: disnake.User,
    title: str,
    description: str = None,
) -> disnake.Embed:
    """Embed template for Timeout"""
    embed = disnake.Embed(title=title, color=disnake.Color.yellow(), description=description)
    utils.add_author_footer(embed, author)
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
            timestamp=utils.get_discord_timestamp(endtime, "Relative Time"),
            reason=reason,
        ),
        inline=False,
    )


async def timeout_embed_listing(
    bot: commands.Bot,
    users: list[TimeoutDB],
    title: str,
    room: disnake.TextChannel,
    author: disnake.User,
) -> None:
    """Embed for sending timeout updates on users"""
    embeds = []
    users_lists = utils.split_to_parts(users, 15)  # to avoid embed char limit
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
    member: disnake.Member,
    starttime: datetime,
    endtime: datetime,
    length: timedelta,
    reason: str,
    isself: bool = False,
    remove_logs: bool = False,
) -> bool:
    """Set timeout for member and update in db. Return True if successful, False otherwise."""
    try:
        if endtime is None:
            await member.timeout(until=None, reason=reason)
            TimeoutDB.remove_timeout(member.id, remove_logs)
        elif length.days > 28:
            await member.timeout(until=datetime.now(timezone.utc) + timedelta(days=28), reason=reason)
            TimeoutDB.add_timeout(
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
            TimeoutDB.add_timeout(
                member.id,
                inter.author.id,
                starttime,
                endtime,
                reason,
                inter.guild.id,
                isself,
            )
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


async def get_user_from_grillbot(owner_id: str, guild_id: str, user_id: str) -> tuple[int, int]:
    """Get unverify count and warning count"""
    headers = {"ApiKey": config.grillbot_api_key, "Author": str(owner_id)}
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10), headers=headers) as session:
        try:
            url = f"{config.grillbot_api_url}/user/info/{guild_id}/{user_id}"
            async with session.get(url) as resp:
                user = await resp.json()
                return user.get("unverifyCount", "Missing"), user.get("warningCount", "Missing")
        except (asyncio.exceptions.TimeoutError, aiohttp.client_exceptions.ClientConnectorError) as e:
            raise ApiError(e)


async def time_check(
    inter: disnake.ApplicationCommandInteraction, endtime: datetime, length: timedelta
) -> bool:
    if endtime < inter.created_at:
        await inter.send(MessagesCZ.past_time, ephemeral=True)
        return True

    if length.total_seconds() < 30:
        await inter.send(MessagesCZ.timeout_too_short, ephemeral=True)
        return True
    return False
