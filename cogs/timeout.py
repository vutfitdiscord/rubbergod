"""
Cog containing timeout commands and manipulating with timeout.
"""
import math
from datetime import datetime, time, timedelta, timezone

import disnake
from disnake.ext import commands, tasks

import features.timeout as features_timeout
import utils
from buttons.embed import EmbedView
from cogs.base import Base
from config import cooldowns
from config.messages import Messages
from database.report import ReportDB
from database.timeout import TimeoutDB, TimeoutUserDB
from permissions import permission_check

timestamps = [
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


async def autocomplete_times(inter, input: str) -> list[str]:
    input = input.lower()
    return [endtime for endtime in timestamps if input in endtime.lower()]


class Timeout(Base, commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.tasks = [self.refresh_timeout.start()]

    @commands.check(permission_check.submod_plus)
    @commands.slash_command(name="timeout", guild_ids=[Base.config.guild_id])
    async def _timeout(self, inter: disnake.ApplicationCommandInteraction): ...

    @_timeout.sub_command(name="user", description=Messages.timeout_brief)
    async def timeout_user(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: str = commands.Param(max_length=1000, description=Messages.timeout_user_param),
        endtime: str = commands.Param(
            autocomplete=autocomplete_times,
            max_length=50,
            description=Messages.time_format,
        ),
        reason: str = commands.Param(max_length=256, description=Messages.timeout_reason_param),
    ):
        """Set timeout for user(s)"""
        parsed_members = await features_timeout.parse_members(inter, user)
        if parsed_members is None:
            return

        endtime: datetime = utils.parse_time(endtime, Messages.time_format)
        # convert to local time
        endtime_local = endtime.astimezone(tz=utils.get_local_zone())
        starttime_local = inter.created_at.astimezone(tz=utils.get_local_zone())
        length = endtime - inter.created_at

        if length.seconds < 30:
            await inter.send(Messages.timeout_too_short, ephemeral=True)
            return

        await inter.response.defer()
        embed = features_timeout.create_embed(inter.author, "Timeout")
        cantBeTimeout = []
        timeoutMembers = []

        for member in parsed_members:
            isSuccess = await features_timeout.timeout_perms(
                inter, member, inter.created_at, endtime, length, reason
            )
            if isSuccess:
                timeoutMembers.append(member)
            else:
                cantBeTimeout.append(member)

            features_timeout.add_field_timeout(
                embed=embed,
                title=member.display_name,
                member=member,
                author=inter.author,
                starttime=starttime_local,
                endtime=endtime_local,
                length=length,
                reason=reason
            )

        if timeoutMembers:
            # print users with timeout if any exists
            message = await inter.original_message()

            await inter.send("".join(f"{member.mention}" for member in parsed_members), embed=embed)
            embed.add_field(name="Link", value=f"[#{inter.channel.name}]({message.jump_url})")
            await self.submod_helper_room.send(
                "".join(f"{member.mention}" for member in parsed_members),
                embed=embed
            )

        if cantBeTimeout:
            # print users that can't be timed out
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
        user: str = commands.Param(max_length=1000, description=Messages.timeout_user_param),
        remove_logs: bool = commands.Param(description=Messages.timeout_remove_logs_param),
    ):
        """Removes timeout from user(s)"""
        embed = features_timeout.create_embed(inter.author, "Timeout remove")
        parsed_members = await features_timeout.parse_members(inter, user)

        if parsed_members is None:
            return

        await inter.response.defer()

        for member in parsed_members:
            await features_timeout.timeout_perms(
                inter, member, None, None, None, "Předčasně odebráno", remove_logs=remove_logs
            )
            embed.add_field(
                name=member.display_name,
                value=Messages.timeout_remove_reason(member=member.mention),
                inline=False
            )

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
        users = TimeoutUserDB.get_active_timeouts(selftimeout)
        await self.update_timeout()

        if not users:
            await inter.send(Messages.timeout_list_none)
            return

        await features_timeout.timeout_embed_listing(self.bot, users, "Timeout list", inter, inter.author)

    @_timeout.sub_command(name="get_user", description=Messages.timeout_get_user_brief)
    async def get_user(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.Member,
    ):
        """List history of timeouts for user"""
        await inter.response.defer()
        timeout_user = TimeoutUserDB.get_user(user.id)
        timeouts_count = len(timeout_user.timeouts) if timeout_user else 0

        embeds = []
        main_embed = features_timeout.create_embed(
            inter.author,
            f"`@{user.display_name}` timeouts",
            user.mention,
        )

        main_embed.add_field(name="Timeouts count", value=timeouts_count, inline=True)
        main_embed.add_field(name="Reports count", value=ReportDB.get_reports_on_user(user.id), inline=True)
        unverifies, warnings = await features_timeout.get_user_from_grillbot(self, inter.guild.id, user.id)
        main_embed.add_field(
            name="Unverifies count",
            value=f"[{unverifies}](https://private.grillbot.eu/admin/unverify/logs)",
            inline=True
        )
        main_embed.add_field(
            name="Warnings count",
            value=f"[{warnings}](https://private.grillbot.eu/admin/userMeasures)",
            inline=True
        )

        recent_timeout = timeout_user.get_last_timeout()
        if timeout_user and recent_timeout is not None:
            author = await self.bot.get_or_fetch_user(recent_timeout.mod_id)
            starttime_local, endtime_local = recent_timeout.start_end_local
            features_timeout.add_field_timeout(
                embed=main_embed,
                title="Recent timeout",
                member=user,
                author=author,
                starttime=starttime_local,
                endtime=endtime_local,
                length=recent_timeout.length,
                reason=recent_timeout.reason
            )
            embeds.append(main_embed)

            embed = features_timeout.create_embed(inter.author, f"`@{user.display_name}` timeouts")
            for index, timeout in enumerate(timeout_user.timeouts[::-1]):           # from newest to oldest
                if (index % 5) == 0 and index != 0:
                    embeds.append(embed)
                    embed = features_timeout.create_embed(inter.author, f"`@{user.display_name}` timeouts")

                author = await self.bot.get_or_fetch_user(timeout.mod_id)
                starttime_local, endtime_local = timeout.start_end_local
                features_timeout.add_field_timeout(
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

        view = EmbedView(inter.author, embeds, show_page=True)
        await inter.send(embed=embeds[0], view=view)
        view.message = await inter.original_message()

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
        starttime_local = inter.created_at.astimezone(tz=utils.get_local_zone())
        length = endtime - inter.created_at

        if length.seconds < 30:
            await inter.send(Messages.timeout_too_short, ephemeral=True)
            return

        await inter.response.defer()
        isSuccess = await features_timeout.timeout_perms(
            inter=inter,
            member=inter.user,
            starttime=starttime_local,
            endtime=endtime,
            length=length,
            reason=Messages.self_timeout_reason,
            isself=True,
        )

        if not isSuccess:
            await inter.send(content=Messages.timeout_permission(user_list=inter.user.mention))
            return

        await inter.send(content=Messages.self_timeout_success)

    async def update_timeout(self):
        """update all user's timeout in database and on server"""
        timeouts = TimeoutUserDB.get_active_timeouts()
        guild = self.bot.get_guild(Base.config.guild_id)

        for timeout in timeouts:
            # find member and update timeout
            member = await guild.get_or_fetch_member(timeout.user_id)

            if member is None:
                # member left server
                continue

            if member.current_timeout is None:
                # someone removed timeout manually
                TimeoutDB.remove_timeout(timeout.user_id)
                continue

            end = timeout.end.astimezone(tz=timezone.utc)
            if (end - datetime.now(timezone.utc)).days > 28:
                await member.timeout(duration=timedelta(days=28), reason=timeout.reason)
            elif member.current_timeout < end:
                await member.timeout(until=end, reason=timeout.reason)

    @tasks.loop(time=time(12, 0, tzinfo=utils.get_local_zone()))
    async def refresh_timeout(self):
        """Update timeout for users saved in db"""
        await self.update_timeout()

        # send update
        users = TimeoutUserDB.get_active_timeouts(isself=False)
        if users:
            await features_timeout.timeout_embed_listing(
                self.bot, users, "Timeout update", self.log_channel, self.bot.user
            )

    @commands.Cog.listener()
    async def on_automod_action_execution(self, execution: disnake.AutoModActionExecution):
        """Add timeout to user if it was added by automod"""
        if isinstance(execution.action, disnake.AutoModTimeoutAction):
            rule = await execution.guild.fetch_automod_rule(execution.rule_id)
            length = timedelta(seconds=execution.action.duration)
            now = datetime.now(timezone.utc)
            TimeoutDB.add_timeout(execution.user_id, 1, now, now + length, rule.name, execution.guild.id)
            # automod actions are sent to submod_helper_room automatically

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
                # remove timeout manually
                TimeoutDB.remove_timeout(entry.target.id)
                embed = features_timeout.create_embed(entry.user, "Timeout remove")
                embed.add_field(
                    name=entry.target.display_name,
                    value=Messages.timeout_manual_remove(member=entry.target.mention),
                    inline=False,
                )

                await self.submod_helper_room.send(embed=embed)

            elif (
                entry.user.current_timeout is None
                and after_timeout is not None
                and entry.user.id != self.bot.user.id
            ):
                # add timeout manually
                length = entry.changes.after.timeout - entry.created_at
                length = timedelta(seconds=math.ceil(length.total_seconds()))   # round up to seconds
                reason = entry.reason or Messages.timeout_manual_timeout
                TimeoutDB.add_timeout(
                    entry.target.id,
                    entry.user.id,
                    entry.created_at,
                    entry.created_at + length,
                    reason,
                    entry.guild.id,
                )
                embed = features_timeout.create_embed(entry.user, "Timeout")
                features_timeout.add_field_timeout(
                    embed=embed,
                    title=entry.target.display_name,
                    member=entry.target,
                    author=entry.user,
                    starttime=entry.created_at,
                    endtime=entry.created_at + length,
                    length=length,
                    reason=reason,
                )

                await self.submod_helper_room.send(embed=embed)


def setup(bot):
    bot.add_cog(Timeout(bot))
