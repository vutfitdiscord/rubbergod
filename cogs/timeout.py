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
from database.timeout import TimeoutDB as TimeoutDB
from permissions import permission_check

timestamps = {
    "60s": 1/60,
    "5min": 5/60,
    "10min": 10/60,
    "1hour": 1,
    "4hours": 4,
    "8hours": 8,
    "12hours": 12,
    "16hours": 16,
    "1day": 1*24,
    "3days": 3*24,
    "1week": 7*24,
    "2weeks": 14*24,
    "3weeks": 21*24,
    "4weeks": 28*24,
    "Forever": -1,
}


async def autocomplete_times(inter, string: str) -> List[str]:
    return [endtime for endtime in timestamps.keys() if string.lower() in endtime.lower()]


class Timeout(Base, commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.timeout_db = TimeoutDB()
        self.formats = ("%d.%m.%Y", "%d/%m/%Y", "%d.%m.%Y %H:%M", "%d/%m/%Y %H:%M")
        self.tasks = [self.refresh_timeout.start()]

    def create_embed(self, author: disnake.User, title: str) -> disnake.Embed:
        """Embed template for Timeout"""
        embed = disnake.Embed(
            title=title,
            color=disnake.Color.yellow()
        )
        utils.add_author_footer(embed, author)
        return embed

    async def timeout_embed_listing(
        self,
        users: List[TimeoutDB],
        title: str,
        room: disnake.TextChannel,
        author: disnake.User
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
                        endtime=timeout.end.strftime('%d.%m.%Y %H:%M'),
                        length=f"{timeout.length.days}d, "
                               f"{timeout.length.seconds // 3600}h, "
                               f"{(timeout.length.seconds // 60) % 60}m"
                    ),
                    value=Messages.timeout_field_text(
                        mod=await self.bot.get_or_fetch_user(timeout.mod_id),
                        starttime=timeout.start.strftime('%d.%m.%Y %H:%M'),
                        length=utils.get_discord_timestamp(timeout.end, "Relative Time"),
                        reason=timeout.reason),
                    inline=False
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
        isself: bool = False
    ) -> bool:
        """Set timeout for member and save in db or remove it"""
        try:
            if length == 0 or endtime is None:
                await member.timeout(until=None, reason=reason)
                self.timeout_db.remove_timeout(member.id)
            elif length.days > 28:
                await member.timeout(until=datetime.now()+timedelta(days=28), reason=reason)
                self.timeout_db.add_timeout(member.id, inter.author.id, starttime, endtime, reason, isself)
            else:
                await member.timeout(until=endtime, reason=reason)
                self.timeout_db.add_timeout(member.id, inter.author.id, starttime, endtime, reason, isself)
            return True
        except disnake.Forbidden:
            return False

    async def parse_members(
        self,
        inter: disnake.ApplicationCommandInteraction,
        members_string: str
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
                    author=inter.author.mention,
                    members=", ".join(not_found_members)
                ),
            )

        return parsed_members or None

    async def timeout_parse(
        self,
        inter: disnake.ApplicationCommandInteraction,
        endtime: str
    ) -> Union[datetime, None]:
        """
        Parse endtime argument and return datetime or None

        Decision tree
        -------------
            if forever:
                return datetime 31.12.9999 00:00:00
            elif timestamp:
                look in timestamps dict, convert to datetime
            else:
                date:
                    convert to datetime
                hours:
                    convert to datetime
        """

        # convert to local time and remove timezone info
        now = inter.created_at.astimezone(tz=utils.get_local_zone()).replace(tzinfo=None)
        if "forever" == endtime.lower():
            endtime = datetime(year=9999, month=12, day=31, hour=0, minute=0, second=0)
            return endtime

        elif endtime in timestamps:
            timeout_duration = timedelta(hours=float(timestamps[endtime]))
            endtime = now + timeout_duration
            return endtime

        else:
            # try to check for date format
            for format in self.formats:
                try:
                    endtime = datetime.strptime(endtime, format)
                    # check for positive timeout length
                    if now > endtime:
                        await inter.send(Messages.timeout_negative_time)
                        return

                    isDate = True
                    break
                except ValueError:
                    isDate = False

            # else convert hours to datetime
            if not isDate:
                try:
                    # check for positive timeout length
                    if float(endtime) < 0:
                        await inter.send(Messages.timeout_negative_time)
                        return

                    # int overflow
                    if len(endtime) > 6:
                        await inter.send(Messages.timeout_overflow)
                        return

                    timeout_duration = timedelta(hours=float(endtime))
                    endtime = now + timeout_duration
                except ValueError:
                    raise commands.BadArgument
        return endtime

    @commands.check(permission_check.submod_plus)
    @commands.slash_command(name="timeout", guild_ids=[Base.config.guild_id])
    async def _timeout(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()

    @_timeout.sub_command(name="user", description=Messages.timeout_brief)
    async def timeout_user(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: str = commands.Param(max_length=1000, description=Messages.timeout_user_brief),
        endtime: str = commands.Param(
            autocomplete=autocomplete_times,
            max_length=20, description=Messages.timeout_time
        ),
        reason: str = commands.Param(max_length=256, description=Messages.timeout_reason)
    ):
        """Set timeout for user(s)"""
        embed = self.create_embed(inter.author, "Timeout")
        parsed_members = await self.parse_members(inter, user)
        cantBeTimeout = []
        timeoutMembers = []

        if parsed_members is None:
            return

        endtime = await self.timeout_parse(inter, endtime)
        # error in parsing
        if endtime is None:
            return

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
                    endtime=endtime.strftime('%d.%m.%Y %H:%M'),
                    length=f"{length.days}d, "
                           f"{length.seconds // 3600}h, "
                           f"{(length.seconds // 60) % 60}m"
                ),
                value=Messages.timeout_field_text(
                    mod=inter.author,
                    starttime=starttime.strftime('%d.%m.%Y %H:%M'),
                    length=utils.get_discord_timestamp(endtime, "Relative Time"),
                    reason=reason
                ),
                inline=False
            )

        # print users with timeout if any exists
        if timeoutMembers:
            message = await inter.original_message()

            await inter.send(''.join(f'{member.mention}' for member in parsed_members), embed=embed)
            embed.add_field(name="Link", value=f"[#{inter.channel.name}]({message.jump_url})")
            await self.submod_helper_room.send(
                ''.join(f'{member.mention}' for member in parsed_members),
                embed=embed
            )

        # print users that can't be timed out
        if cantBeTimeout:
            await inter.send('\n'.join(
                Messages.timeout_permission(user_list=user.name) for user in cantBeTimeout)
            )

    @_timeout.sub_command(name="remove", description=Messages.timeout_remove_brief)
    async def remove_timeout(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: str = commands.Param(max_length=1000, description=Messages.timeout_user_brief)
    ):
        """Removes timeout from user(s)"""
        embed = self.create_embed(inter.author, "Timeout remove")
        parsed_members = await self.parse_members(inter, user)

        if parsed_members is None:
            return

        for member in parsed_members:
            await self.timeout_perms(inter, member, None, None, None, "Předčasné odebrání")
            embed.add_field(name=member, value="Předčasně odebráno", inline=False)

        await self.submod_helper_room.send(embed=embed)
        await inter.send(embed=embed)

    @_timeout.sub_command(name="list", description=Messages.timeout_list_brief)
    async def timeout_list(
        self,
        inter: disnake.ApplicationCommandInteraction,
        selftimeout: bool = commands.Param(default=False)
    ):
        """List all timed out users"""
        await self.update_timeout()

        users = self.timeout_db.get_timeout_users_filter_self(selftimeout)
        if not users:
            await inter.send(Messages.timeout_list_none)
            return

        await self.timeout_embed_listing(users, "Timeout list", inter, inter.author)

    @cooldowns.default_cooldown
    @commands.slash_command(
        name="selftimeout",
        description=Messages.self_timeout,
        guild_ids=[Base.config.guild_id]
    )
    async def self_timeout(
        self,
        inter: disnake.ApplicationCommandInteraction,
        endtime: str = commands.Param(
            autocomplete=autocomplete_times,
            max_length=20, description=Messages.timeout_time
        )
    ):
        # Guild_id is used to prevent users from bypassing timeout
        # given by moderator and using selftimeout in DMs

        await inter.response.defer(ephemeral=True)
        endtime = await self.timeout_parse(inter, endtime)
        starttime = inter.created_at.astimezone(tz=utils.get_local_zone()).replace(tzinfo=None)
        length = endtime - starttime

        isSuccess = await self.timeout_perms(
            inter,
            inter.user,
            starttime,
            endtime,
            length,
            Messages.self_timeout_reason,
            True
        )

        if not isSuccess:
            await inter.send(content=Messages.timeout_permission(user_list=inter.user.mention))
            return

        await inter.send(content=Messages.self_timeout_success)

    async def update_timeout(self):
        """update all user's timeout in database and on server"""
        users = self.timeout_db.get_timeout_users()
        guild = self.bot.get_guild(self.config.guild_id)

        # find member and update timeout
        for user in users:
            member = guild.get_member(user.user_id)

            # member left server
            if member is None:
                if user.end < datetime.now():
                    self.timeout_db.remove_timeout(user.user_id)
                continue

            # someone removed timeout manually
            if member.current_timeout is None:
                self.timeout_db.remove_timeout(user.user_id)
                continue

            # get timezone aware datetime object
            current_timeout = member.current_timeout.astimezone(tz=utils.get_local_zone())
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
        users = self.timeout_db.get_timeout_users_filter_self(isself=False)
        if users:
            await self.timeout_embed_listing(users, "Timeout Update", self.log_channel, self.bot.user)

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
                self.timeout_db.remove_timeout(entry.target.id)
                embed = self.create_embed(entry.user, "Timeout remove")
                embed.add_field(name=entry.target, value="Předčasně odebráno", inline=False)

                await self.submod_helper_room.send(embed=embed)

    @self_timeout.error
    @timeout_user.error
    async def timeout_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.BadArgument):
            await inter.send(Messages.timeout_bad_format(format="\n".join(self.formats)))
            return True


def setup(bot):
    bot.add_cog(Timeout(bot))
