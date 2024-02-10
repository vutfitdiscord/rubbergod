import shlex
from datetime import datetime, timedelta, timezone

import disnake
from disnake.ext import commands

import utils
from config.messages import Messages
from database.timeout import TimeoutDB


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
    member: disnake.Member,
    author: disnake.Member,
    starttime: datetime,
    endtime: datetime,
    length: timedelta,
    reason: str,
):
    embed.add_field(
        name=title,
        value=Messages.timeout_field_text(
            member=f"{member.mention} ({member.display_name})",
            mod=f"{author.mention} ({author.display_name})",
            starttime=starttime.strftime("%d.%m.%Y %H:%M"),
            endtime=endtime.strftime("%d.%m.%Y %H:%M"),
            length=f"{length.days}d, "
            f"{length.seconds // 3600}h, "
            f"{(length.seconds // 60) % 60}m",
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
    users_lists = utils.split_to_parts(users, 15)       # to avoid embed char limit
    for users_list in users_lists:
        embed = create_embed(author, title)
        for timeout in users_list:
            starttime_local, endtime_local = timeout.local_time
            member = await bot.get_or_fetch_user(timeout.user_id)
            add_field_timeout(
                embed=embed,
                title=member.display_name,
                member=member,
                author=author,
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
        if length == 0 or endtime is None:
            await member.timeout(until=None, reason=reason)
            TimeoutDB.remove_timeout(member.id, remove_logs)
        elif length.days > 28:
            await member.timeout(until=datetime.now(timezone.utc) + timedelta(days=28), reason=reason)
            TimeoutDB.add_timeout(
                member.id, inter.author.id, starttime, endtime, reason, inter.guild.id, isself,
            )
        else:
            await member.timeout(until=endtime, reason=reason)
            TimeoutDB.add_timeout(
                member.id, inter.author.id, starttime, endtime, reason, inter.guild.id, isself,
            )
        return True
    except disnake.Forbidden:
        # bot can't timeout member
        return False


async def parse_members(
    inter: disnake.ApplicationCommandInteraction,
    members_string: str
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
            Messages.timeout_member_not_found(
                author=inter.author.mention, members=", ".join(not_found_members)
            ),
            ephemeral=True
        )

    return parsed_members or None
