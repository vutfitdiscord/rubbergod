"""
Cog containing timeout commands and manipulating with timeout.
"""

import shlex
from datetime import datetime, time, timedelta
from typing import List, Union

import disnake
from disnake.ext import commands, tasks

import utils
from cogs.base import Base
from config import cooldowns
from config.messages import Messages
from database.timeout import TimeoutDB
from permissions import permission_check

timestamps = {
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
}


async def autocomplete_times(inter, input: str) -> List[str]:
    input = input.lower()
    return [endtime for endtime in timestamps if input in endtime.lower()]


class Timeout(Base, commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.tasks = [self.refresh_timeout.start()]

    def create_embed(self, author: disnake.User, title: str) -> disnake.Embed:
        """Embed template for Timeout"""
        embed = disnake.Embed(title=title, color=disnake.Color.yellow())
        utils.add_author_footer(embed, author)
        return embed

    async def timeout_embed_listing(
        self,
        users: List[TimeoutDB],
        title: str,
        room: disnake.TextChannel,
        author: disnake.User,
    ) -> None:
        """Embed for sending timeout updates on users"""
        embeds = []
        # max 25 fields per embed
        users_lists = utils.split_to_parts(users, 25)
        for users_list in users_lists:
            embed = self.create_embed(author, title)
            for timeout in users_list:
                embed.add_field(
                    name=Messages.timeout_title(
                        member=await self.bot.get_or_fetch_user(timeout.user_id),
                        endtime=timeout.end.strftime("%d.%m.%Y %H:%M"),
                        length=f"{timeout.length.days}d, "
                        f"{timeout.length.seconds // 3600}h, "
                        f"{(timeout.length.seconds // 60) % 60}m",
                    ),
                    value=Messages.timeout_field_text(
                        mod=await self.bot.get_or_fetch_user(timeout.mod_id),
                        starttime=timeout.start.strftime("%d.%m.%Y %H:%M"),
                        length=utils.get_discord_timestamp(timeout.end, "Relative Time"),
                        reason=timeout.reason,
                    ),
                    inline=False,
                )
            embeds.append(embed)
        await room.send(embeds=embeds)

    async def timeout_perms(
        self,
        inter: disnake.ApplicationCommandInteraction,
        member: disnake.Member,
        starttime: datetime,
        endtime: datetime,
        length: timedelta,
        reason: str,
        isself: bool = False,
    ) -> bool:
        """Set timeout for member and update in db. Return True if successful, False otherwise."""
        try:
            if length == 0 or endtime is None:
                await member.timeout(until=None, reason=reason)
                TimeoutDB.remove_timeout(member.id)
            elif length.days > 28:
                await member.timeout(until=datetime.now() + timedelta(days=28), reason=reason)
                TimeoutDB.add_timeout(member.id, inter.author.id, starttime, endtime, reason, isself)
            else:
                await member.timeout(until=endtime, reason=reason)
                TimeoutDB.add_timeout(member.id, inter.author.id, starttime, endtime, reason, isself)
            return True
        except disnake.Forbidden:
            return False

    async def parse_members(
        self, inter: disnake.ApplicationCommandInteraction, members_string: str
    ) -> Union[List[disnake.Member], None]:
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

        # print users that can't be found
        if not_found_members:
            await inter.send(
                Messages.timeout_member_not_found(
                    author=inter.author.mention, members=", ".join(not_found_members)
                ),
            )

        return parsed_members or None

    @commands.check(permission_check.submod_plus)
    @commands.slash_command(name="timeout", guild_ids=[Base.config.guild_id])
    async def _timeout(self, inter: disnake.ApplicationCommandInteraction): ...

    @_timeout.sub_command(name="user", description=Messages.timeout_brief)
    async def timeout_user(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: str = commands.Param(max_length=1000, description=Messages.timeout_user_brief),
        endtime: str = commands.Param(
            autocomplete=autocomplete_times,
            max_length=50,
            description=Messages.time_format,
        ),
        reason: str = commands.Param(max_length=256, description=Messages.timeout_reason),
    ):
        """Set timeout for user(s)"""
        embed = self.create_embed(inter.author, "Timeout")
        parsed_members = await self.parse_members(inter, user)
        cantBeTimeout = []
        timeoutMembers = []

        if parsed_members is None:
            return

        endtime = utils.parse_time(endtime, Messages.time_format)

        await inter.response.defer()

        # convert to local time and remove timezone info
        endtime = endtime.replace(tzinfo=utils.get_local_zone()).replace(tzinfo=None)
        starttime = inter.created_at.astimezone(tz=utils.get_local_zone()).replace(tzinfo=None)
        length = endtime - starttime

        for member in parsed_members:
            isSuccess = await self.timeout_perms(inter, member, starttime, endtime, length, reason)
            if isSuccess:
                timeoutMembers.append(member)
            else:
                cantBeTimeout.append(member)

            embed.add_field(
                name=Messages.timeout_title(
                    member=member,
                    endtime=endtime.strftime("%d.%m.%Y %H:%M"),
                    length=f"{length.days}d, "
                    f"{length.seconds // 3600}h, "
                    f"{(length.seconds // 60) % 60}m",
                ),
                value=Messages.timeout_field_text(
                    mod=inter.author,
                    starttime=starttime.strftime("%d.%m.%Y %H:%M"),
                    length=utils.get_discord_timestamp(endtime, "Relative Time"),
                    reason=reason,
                ),
                inline=False,
            )

        # print users with timeout if any exists
        if timeoutMembers:
            message = await inter.original_message()

            await inter.send("".join(f"{member.mention}" for member in parsed_members), embed=embed)
            embed.add_field(name="Link", value=f"[#{inter.channel.name}]({message.jump_url})")
            await self.submod_helper_room.send(
                "".join(f"{member.mention}" for member in parsed_members),
                embed=embed
            )

        # print users that can't be timed out
        if cantBeTimeout:
            await inter.send(
                "\n".join(
                    Messages.timeout_permission(user_list=user.name)
                    for user in cantBeTimeout
                ),
                ephemeral=True,
            )

    @_timeout.sub_command(name="remove", description=Messages.timeout_remove_brief)
    async def remove_timeout(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: str = commands.Param(max_length=1000, description=Messages.timeout_user_brief),
    ):
        """Removes timeout from user(s)"""
        embed = self.create_embed(inter.author, "Timeout remove")
        parsed_members = await self.parse_members(inter, user)

        if parsed_members is None:
            return

        await inter.response.defer()

        for member in parsed_members:
            await self.timeout_perms(inter, member, None, None, None, "Předčasné odebrání")
            embed.add_field(name=member, value="Předčasně odebráno", inline=False)

        await self.submod_helper_room.send(embed=embed)
        await inter.send(embed=embed)

    @_timeout.sub_command(name="list", description=Messages.timeout_list_brief)
    async def timeout_list(
        self,
        inter: disnake.ApplicationCommandInteraction,
        selftimeout: bool = commands.Param(default=False),
    ):
        """List all timed out users"""
        await inter.response.defer()
        await self.update_timeout()

        users = TimeoutDB.get_timeout_users_filter_self(selftimeout)
        if not users:
            await inter.send(Messages.timeout_list_none)
            return

        await self.timeout_embed_listing(users, "Timeout list", inter, inter.author)

    @cooldowns.default_cooldown
    @commands.slash_command(
        name="selftimeout",
        description=Messages.self_timeout,
        guild_ids=[Base.config.guild_id],
    )
    async def self_timeout(
        self,
        inter: disnake.ApplicationCommandInteraction,
        endtime: str = commands.Param(
            autocomplete=autocomplete_times,
            max_length=50,
            description=Messages.time_format,
        ),
    ):
        """Set timeout for yourself.
        Guild_ids is used to prevent users from bypassing timeout
        given by moderator and using selftimeout in DMs.
        """

        endtime = utils.parse_time(endtime, Messages.time_format)
        await inter.response.defer()

        starttime = inter.created_at.astimezone(tz=utils.get_local_zone()).replace(tzinfo=None)
        length = endtime - starttime

        isSuccess = await self.timeout_perms(
            inter,
            inter.user,
            starttime,
            endtime,
            length,
            Messages.self_timeout_reason,
            True,
        )

        if not isSuccess:
            await inter.send(content=Messages.timeout_permission(user_list=inter.user.mention))
            return

        await inter.send(content=Messages.self_timeout_success)

    async def update_timeout(self):
        """update all user's timeout in database and on server"""
        users = TimeoutDB.get_timeout_users()
        guild = self.bot.get_guild(self.config.guild_id)

        # find member and update timeout
        for user in users:
            member = guild.get_member(user.user_id)

            # member left server
            if member is None:
                if user.end < datetime.now():
                    TimeoutDB.remove_timeout(user.user_id)
                continue

            # someone removed timeout manually
            if member.current_timeout is None:
                TimeoutDB.remove_timeout(user.user_id)
                continue

            # get timezone aware datetime object
            current_timeout = member.current_timeout.astimezone(
                tz=utils.get_local_zone()
            )
            end_timeout = user.end.replace(tzinfo=utils.get_local_zone())

            if (user.end - datetime.now()).days > 28:
                await member.timeout(duration=timedelta(days=28), reason=user.reason)
            elif current_timeout < end_timeout:
                await member.timeout(until=user.end, reason=user.reason)

    @tasks.loop(time=time(12, 0, tzinfo=utils.get_local_zone()))
    async def refresh_timeout(self):
        """Update timeout for users saved in db"""
        await self.update_timeout()

        # send update
        users = TimeoutDB.get_timeout_users_filter_self(isself=False)
        if users:
            await self.timeout_embed_listing(
                users, "Timeout Update", self.log_channel, self.bot.user
            )

    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry: disnake.AuditLogEntry):
        """Remove timeout from user if it was removed manually. Send message to submod_helper_room"""
        if entry.action == disnake.AuditLogAction.member_update:
            before_timeout = getattr(entry.changes.before, "timeout", None)
            after_timeout = getattr(entry.changes.after, "timeout", None)

            if (
                before_timeout is not None
                and after_timeout is None
                and entry.user.id != self.bot.user.id
            ):
                TimeoutDB.remove_timeout(entry.target.id)
                embed = self.create_embed(entry.user, "Timeout remove")
                embed.add_field(
                    name=entry.target, value="Předčasně odebráno", inline=False
                )

                await self.submod_helper_room.send(embed=embed)


def setup(bot):
    bot.add_cog(Timeout(bot))
