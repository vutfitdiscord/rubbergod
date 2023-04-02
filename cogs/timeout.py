"""
Containing timeout commands and manipulating with timeout.
"""

from datetime import datetime, time, timedelta
from functools import cached_property
from typing import List

import disnake
from disnake.ext import commands, tasks

import utils
from config.app_config import config
from config.messages import Messages
from permissions import permission_check
from repository.timeout_repo import TimeoutRepository

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


class Timeout(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.timeout_repo = TimeoutRepository()
        self.formats = ("%d.%m.%Y", "%d/%m/%Y", "%d.%m.%Y %H:%M", "%d/%m/%Y %H:%M")
        self.refresh_timeout.start()
        self.perms_users = []

    @cached_property
    def submod_helper_room(self):
        return self.bot.get_channel(config.submod_helper_room)

    def create_embed(self, author, title):
        """Embed template for Timeout"""
        embed = disnake.Embed(
            title=title,
            color=disnake.Color.yellow()
        )
        utils.add_author_footer(embed, author)
        return embed

    async def timeout_embed_listing(self, users, title, room, author):
        """Embed for sending timeout updates on users"""
        embeds = []
        # max 25 fields per embed
        users_lists = utils.split_to_parts(users, 25)
        for users_list in users_lists:
            embed = self.create_embed(author, title)
            for timeout in users_list:
                embed.add_field(
                    name=Messages.timeout_title.format(
                        user=self.bot.get_user(timeout.user_id),
                        endtime=(timeout.end).strftime('%d.%m.%Y %H:%M')
                    ),
                    value=Messages.timeout_field_text.format(
                        mod=self.bot.get_user(timeout.mod_id),
                        reason=timeout.reason),
                    inline=False
                )
            embeds.append(embed)
        await room.send(embeds=embeds)

    async def timeout_perms(self, inter, user, duration, endtime, reason) -> bool:
        """Set timeout for user or remove it and save in db"""
        try:
            await user.timeout(duration=duration, reason=reason)
            if duration is None:
                self.timeout_repo.remove_timeout(user.id)
            else:
                self.timeout_repo.add_timeout(user.id, inter.author.id, endtime, reason)
            return False
        except disnake.Forbidden:
            self.perms_users.append(user)
            return True

    async def timeout_parse(self, inter, user, endtime, reason):
        """Parse time argument to timedelta(lenght)"""
        if "forever" == endtime.lower():
            endtime = datetime.now().replace(year=datetime.now().year+1000)
            if await self.timeout_perms(inter, user, timedelta(days=28), endtime, reason):
                return

        elif endtime in timestamps:
            timeout_duration = timedelta(hours=float(timestamps[endtime]))
            endtime = datetime.now() + timeout_duration
            if await self.timeout_perms(inter, user, timeout_duration, endtime, reason):
                return

        else:
            # try to check for date format
            for format in self.formats:
                try:
                    endtime = datetime.strptime(endtime, format)

                    # check for positive timeout lenght
                    if datetime.now() > endtime:
                        await inter.send(Messages.timeout_negative_time)
                        return

                    timeout_duration = endtime - datetime.now()
                    date = True
                    break
                except ValueError:
                    date = False

            # else convert hours to deltatime
            if not date:
                try:
                    # check for positive timeout lenght
                    if float(endtime) <= 0:
                        await inter.send(Messages.timeout_negative_time)
                        return

                    # int overflow
                    if len(endtime) > 7:
                        await inter.send(Messages.timeout_overflow)
                        return

                    timeout_duration = timedelta(hours=float(endtime))
                    endtime = datetime.now() + timeout_duration
                except ValueError:
                    raise commands.BadArgument

            # maximum lenght for timeout is 28 days set by discord
            if timeout_duration.days > 28:
                if await self.timeout_perms(inter, user, timedelta(days=28), endtime, reason):
                    return
            else:
                if await self.timeout_perms(inter, user, timeout_duration, endtime, reason):
                    return
        return endtime

    @commands.check(permission_check.submod_plus)
    @commands.slash_command(name="timeout", guild_ids=[config.guild_id])
    async def _timeout(self, inter):
        pass

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
        await inter.response.defer()
        members = await utils.get_members_from_tag(inter.guild, user)
        embed = self.create_embed(inter.author, "Timeout")
        timeout_members = False

        # no member found
        if not members:
            return await inter.send(utils.fill_message("member_not_found", user=inter.author.id))

        for user in members:
            parsed_endtime = await self.timeout_parse(inter, user, endtime, reason)
            # if error in parsing return
            if parsed_endtime is None:
                continue

            timeout_members = True
            embed.add_field(
                name=f"{user} | {parsed_endtime.strftime('%d.%m.%Y %H:%M')}",
                value=f"**Důvod:** {reason}",
                inline=False
            )

        # print users with timeout
        if timeout_members:
            message = await inter.original_message()

            await inter.send(''.join(f'{user.mention}' for user in members), embed=embed)
            embed.add_field(name="Link", value=f"[#{inter.channel.name}]({message.jump_url})")
            await self.submod_helper_room.send(''.join(f'{user.mention}' for user in members), embed=embed)

        # print users that can't be timed out
        if self.perms_users:
            await inter.followup.send('\n'.join(
                    f'{Messages.timeout_permission.format(user=user.name)}'for user in self.perms_users)
            )
            self.perms_users = []

    @_timeout.sub_command(name="remove", description=Messages.timeout_remove_brief)
    async def remove_timeout(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: str = commands.Param(max_length=1000, description=Messages.timeout_user_brief)
    ):
        """Removes timeout from user(s)"""
        members = await utils.get_members_from_tag(inter.guild, user)
        embed = self.create_embed(inter.author, "Timeout remove")

        # no member found
        if not members:
            return await inter.send(utils.fill_message("member_not_found", user=inter.author.id))

        for user in members:
            if await self.timeout_perms(inter, user, None, None, "Předčasné odebrání"):
                continue
            embed.add_field(name=user, value="Předčasně odebráno", inline=False)

        await self.submod_helper_room.send(embed=embed)
        await inter.send(embed=embed)

    @_timeout.sub_command(name="list", description=Messages.timeout_list_brief)
    async def timeout_list(
        self,
        inter: disnake.ApplicationCommandInteraction,
    ):
        """List all timed out users"""
        users = self.timeout_repo.get_timeout_users()
        if not users:
            await inter.send("Nikoho jsem nenašel.")
            return

        await self.timeout_embed_listing(users, "Timeout list", inter, inter.author)

    @tasks.loop(time=time(12, 0, tzinfo=utils.get_local_zone()))
    async def refresh_timeout(self):
        """Update timeout for users saved in db"""
        users = self.timeout_repo.get_timeout_users()

        # find member and update timeout
        for user in users:
            guild = self.bot.get_guild(config.guild_id)
            member = guild.get_member(user.user_id)

            # member left server
            if member is None:
                continue

            # someone removed timeout manually
            if member.current_timeout is None:
                self.timeout_repo.remove_timeout(user.user_id)
                continue

            current_timeout = member.current_timeout.astimezone(tz=utils.get_local_zone())
            end_timeout = user.end.replace(tzinfo=utils.get_local_zone())

            if (user.end - datetime.now()).days > 28:
                await member.timeout(duration=timedelta(days=28), reason=user.reason)
            elif current_timeout < end_timeout:
                await member.timeout(until=user.end, reason=user.reason)

        # send update
        users = self.timeout_repo.get_timeout_users()
        await self.timeout_embed_listing(users, "Timeout Update", self.submod_helper_room, self.bot.user)

    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry):
        """Remove timeout from user if it was removed manually. Send message to submod_helper_room"""
        if entry.action == disnake.AuditLogAction.member_update:
            before_timeout = getattr(entry.changes.before, "timeout", None)
            after_timeout = getattr(entry.changes.after, "timeout", None)

            if (
                before_timeout is not None
                and after_timeout is None
                and entry.user.id != self.bot.user.id
            ):
                self.timeout_repo.remove_timeout(entry.target.id)
                embed = self.create_embed(entry.user, "Timeout remove")
                embed.add_field(name=entry.target, value="Předčasně odebráno", inline=False)

                await self.submod_helper_room.send(embed=embed)

    @timeout_user.error
    async def timeout_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.BadArgument):
            await inter.send(Messages.timeout_bad_format.format(format="\n".join(self.formats)))
            return True


def setup(bot):
    bot.add_cog(Timeout(bot))
