"""
Cog containing timeout commands and manipulating with timeout.
"""

import math
from datetime import datetime, time, timedelta, timezone

import disnake
from disnake.ext import commands, tasks

import utils
from buttons.embed import EmbedView
from cogs.base import Base
from cogs.timeoutwars.messages_cz import MessagesCZ as TimeoutWarsMessages
from config import cooldowns
from database.timeout import TimeoutDB, TimeoutUserDB
from permissions import permission_check
from rubbergod import Rubbergod

from . import features
from .messages_cz import MessagesCZ

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


async def autocomplete_times(inter: disnake.ApplicationCommandInteraction, input: str) -> list[str]:
    input = input.lower()
    return [endtime for endtime in timestamps if input in endtime.lower()]


class Timeout(Base, commands.Cog):
    def __init__(self, bot: Rubbergod):
        super().__init__()
        self.bot = bot
        self.tasks = [self.refresh_timeout.start()]

    @commands.check(permission_check.submod_plus)
    @commands.slash_command(name="timeout", guild_ids=[Base.config.guild_id])
    async def _timeout(self, inter: disnake.ApplicationCommandInteraction): ...

    @_timeout.sub_command(name="user", description=MessagesCZ.timeout_brief)
    async def timeout_user(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: str = commands.Param(max_length=1000, description=MessagesCZ.user_param),
        endtime: str = commands.Param(
            autocomplete=autocomplete_times,
            max_length=50,
            description=MessagesCZ.time_format,
        ),
        reason: str = commands.Param(max_length=256, description=MessagesCZ.reason_param),
    ):
        """Set timeout for user(s)"""
        parsed_members = await features.parse_members(inter, user)
        if parsed_members is None:
            return

        endtime_datetime = utils.general.parse_time(endtime, MessagesCZ.time_format)
        length = endtime_datetime - inter.created_at
        if await features.time_check(inter, endtime_datetime, length):
            return

        # convert to local time
        endtime_local = endtime_datetime.astimezone(tz=utils.general.get_local_zone())  # type: ignore
        starttime_local = inter.created_at.astimezone(tz=utils.general.get_local_zone())

        await inter.response.defer()
        embed = features.create_embed(inter.author, "Timeout")
        cantBeTimeout = []
        timeoutMembers = []

        for member in parsed_members:
            isSuccess = await features.timeout_perms(
                inter=inter,
                session=self.bot.grillbot_session,
                bot_dev_channel=self.bot_dev_channel,
                member=member,
                starttime=inter.created_at,
                endtime=endtime_datetime,
                length=length,
                reason=reason,
            )
            if isSuccess:
                timeoutMembers.append(member)
            else:
                cantBeTimeout.append(member)

            features.add_field_timeout(
                embed=embed,
                title=member.display_name,
                member=member,
                author=inter.author,
                starttime=starttime_local,
                endtime=endtime_local,
                length=length,
                reason=reason,
            )

        if timeoutMembers:
            # print users with timeout if any exists
            message = await inter.original_message()

            await inter.send("".join(f"{member.mention}" for member in parsed_members), embed=embed)
            embed.add_field(name="Link", value=f"[#{inter.channel.name}]({message.jump_url})")
            await self.submod_helper_room.send(
                "".join(f"{member.mention}" for member in parsed_members), embed=embed
            )

        if cantBeTimeout:
            # print users that can't be timed out
            await inter.send(
                "\n".join(MessagesCZ.missing_permission(user_list=user.name) for user in cantBeTimeout),
                ephemeral=True,
            )

    @_timeout.sub_command(name="remove", description=MessagesCZ.remove_brief)
    async def remove_timeout(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: str = commands.Param(max_length=1000, description=MessagesCZ.user_param),
        remove_logs: bool = commands.Param(description=MessagesCZ.remove_logs_param),
    ):
        """Removes timeout from user(s)"""
        embed = features.create_embed(inter.author, "Timeout remove")
        parsed_members = await features.parse_members(inter, user)

        if parsed_members is None:
            return

        await inter.response.defer()

        for member in parsed_members:
            await features.timeout_perms(
                inter=inter,
                session=self.bot.grillbot_session,
                bot_dev_channel=self.bot_dev_channel,
                member=member,
                starttime=None,
                endtime=None,
                length=None,
                reason="Předčasně odebráno",
                remove_logs=remove_logs,
            )
            embed.add_field(
                name=member.display_name,
                value=MessagesCZ.remove_reason(member=member.mention),
                inline=False,
            )

        await self.submod_helper_room.send(embed=embed)
        await inter.send(embed=embed)

    @_timeout.sub_command(name="list", description=MessagesCZ.list_brief)
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
            await inter.send(MessagesCZ.list_none)
            return

        await features.timeout_embed_listing(self.bot, users, "Timeout list", inter, inter.author)

    @_timeout.sub_command(name="get_user", description=MessagesCZ.get_user_brief)
    async def get_user(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User,
    ):
        """List history of timeouts for user"""
        await inter.response.defer()
        embeds = await features.timeout_get_user(inter.author, inter.guild.id, self.bot, user)
        view = EmbedView(inter.author, embeds, show_page=True)
        await inter.send(embed=embeds[0], view=view)
        view.message = await inter.original_message()

    @cooldowns.default_cooldown
    @commands.slash_command(
        name="selftimeout",
        description=MessagesCZ.self_timeout_brief,
        guild_ids=[Base.config.guild_id],
    )
    async def self_timeout(
        self,
        inter: disnake.ApplicationCommandInteraction,
        endtime: str = commands.Param(
            autocomplete=autocomplete_times,
            max_length=50,
            description=MessagesCZ.time_format,
        ),
    ):
        """Set timeout for yourself.
        Guild_ids is used to prevent users from bypassing timeout
        given by moderator and using selftimeout in DMs.
        """
        endtime_datetime = utils.general.parse_time(endtime, MessagesCZ.time_format)
        starttime_local = inter.created_at.astimezone(tz=utils.general.get_local_zone())
        length = endtime_datetime - inter.created_at

        if await features.time_check(inter, endtime_datetime, length):
            return

        await inter.response.defer()
        isSuccess = await features.timeout_perms(
            inter=inter,
            session=self.bot.grillbot_session,
            bot_dev_channel=self.bot_dev_channel,
            member=inter.user,
            starttime=starttime_local,
            endtime=endtime_datetime,
            length=length,
            reason=MessagesCZ.self_timeout_reason,
            isself=True,
        )

        if not isSuccess:
            await inter.send(content=MessagesCZ.missing_permission(user_list=inter.user.mention))
            return

        await inter.send(content=MessagesCZ.self_timeout_success)

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

    @tasks.loop(time=time(12, 0, tzinfo=utils.general.get_local_zone()))
    async def refresh_timeout(self):
        """Update timeout for users saved in db"""
        await self.update_timeout()

        # send update
        users = TimeoutUserDB.get_active_timeouts(isself=False)
        if users:
            await features.timeout_embed_listing(
                self.bot, users, "Timeout update", self.log_channel, self.bot.user
            )

    @commands.Cog.listener()
    async def on_automod_action_execution(self, execution: disnake.AutoModActionExecution):
        """Add timeout to user if it was added by automod"""
        if isinstance(execution.action, disnake.AutoModTimeoutAction):
            rule = await execution.guild.fetch_automod_rule(execution.rule_id)
            length = timedelta(seconds=execution.action.duration)
            now = datetime.now(timezone.utc)
            timeout = TimeoutDB.add_timeout(
                execution.user_id, "1", now, now + length, rule.name, execution.guild.id
            )
            error = await features.send_to_grillbot(self.bot.grillbot_session, timeout)
            if error:
                await self.bot_dev_channel.send(error)
            # automod actions are sent to submod_helper_room automatically

    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry: disnake.AuditLogEntry):
        """Remove timeout from user if it was removed manually. Send message to submod_helper_room"""
        if entry.action == disnake.AuditLogAction.member_update:
            before_timeout = getattr(entry.changes.before, "timeout", None)
            after_timeout = getattr(entry.changes.after, "timeout", None)

            if before_timeout is not None and after_timeout is None and entry.user.id != self.bot.user.id:
                # remove timeout manually
                TimeoutDB.remove_timeout(entry.target.id)
                embed = features.create_embed(entry.user, "Timeout remove")
                embed.add_field(
                    name=entry.target.display_name,
                    value=MessagesCZ.manual_remove(member=entry.target.mention),
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
                length = timedelta(seconds=math.ceil(length.total_seconds()))  # round up to seconds
                reason = entry.reason or MessagesCZ.manual_timeout
                if reason == TimeoutWarsMessages.timeout_wars_reason:
                    # timeout was added during timeout wars 1. April
                    return

                timeout = TimeoutDB.add_timeout(
                    entry.target.id,
                    entry.user.id,
                    entry.created_at,
                    entry.created_at + length,
                    reason,
                    entry.guild.id,
                )
                start = entry.created_at.astimezone(tz=utils.general.get_local_zone())
                embed = features.create_embed(entry.user, "Timeout")
                features.add_field_timeout(
                    embed=embed,
                    title=entry.target.display_name,
                    member=entry.target,
                    author=entry.user,
                    starttime=start,
                    endtime=start + length,
                    length=length,
                    reason=reason,
                )

                await self.submod_helper_room.send(embed=embed)
                error = await features.send_to_grillbot(self.bot.grillbot_session, timeout)
                if error:
                    await self.bot_dev_channel.send(error)
