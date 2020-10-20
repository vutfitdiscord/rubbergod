import discord
from discord.ext import commands

import utils
import re
import datetime
from config import app_config as config, messages
from features import karma
from repository import karma_repo
from cogs import room_check


karma_r = karma_repo.KarmaRepository()
config = config.Config
messages = messages.Messages


class Karma(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.karma = karma.Karma(bot, karma_r)
        self.check = room_check.RoomCheck(bot)

    async def hadle_reaction(self, ctx):
        # grillbot emoji for removing message causes errors
        if ctx["emoji"] == "⏹️":
            return
        # handle karma vote
        elif ctx["message"].content.startswith(messages.karma_vote_message_hack):
            if ctx["emoji"] not in ["✅", "❌", "0⃣"]:
                await ctx["message"].remove_reaction(ctx["emoji"], ctx["member"])
            else:
                users = []
                for reaction in ctx["message"].reactions:
                    users.append(await reaction.users().flatten())
                # Flatten the final list
                users = [x for y in users for x in y]
                if users.count(ctx["member"]) > 1:
                    await ctx["message"].remove_reaction(ctx["emoji"], ctx["member"])
        # leaderboard pagination
        elif (
            ctx["message"].embeds
            and ctx["message"].embeds[0].title is not discord.Embed.Empty
            and re.match(r".* (LEADER|BAJKAR|ISHA|GIVING)BOARD .*", ctx["message"].embeds[0].title)
            and ctx["emoji"] in ["◀", "▶", "⏪"]
        ):
            embed = ctx["message"].embeds[0]
            column, attribute, max_page = self.karma.get_db_from_title(embed.title)
            if column is None:
                return

            if not embed.description is discord.Embed.Empty:
                current_page = int(embed.description.split(" – ")[0])
            else:
                current_page = max_page
            if ctx["emoji"] == "▶":
                next_page = current_page + 10
                if next_page > max_page - 9:
                    next_page = max_page - 9
            elif ctx["emoji"] == "◀":
                next_page = current_page - 10
                if next_page <= 0:
                    next_page = 1
            elif ctx["emoji"] == "⏪":
                next_page = 1
            embed.description = self.karma.gen_leaderboard_content(attribute, next_page, column)
            embed.timestamp = datetime.datetime.now(tz=datetime.timezone.utc)
            await ctx["message"].edit(embed=embed)
            if ctx["message"].guild:
                await ctx["message"].remove_reaction(ctx["emoji"], ctx["member"])
        # handle karma
        elif (
            ctx["member"].id != ctx["message"].author.id
            and ctx["guild"].id == config.guild_id
            and ctx["message"].channel.id not in config.karma_banned_channels
            and config.karma_ban_role_id not in map(lambda x: x.id, ctx["member"].roles)
        ):
            if isinstance(ctx["emoji"], str):
                karma_r.karma_emoji(ctx["message"].author, ctx["member"], ctx["emoji"])
            else:
                karma_r.karma_emoji(ctx["message"].author, ctx["member"], ctx["emoji"].id)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        ctx = await utils.reaction_get_ctx(self.bot, payload)
        if ctx is None:
            return

        if (
            ctx["member"].id != ctx["message"].author.id
            and ctx["guild"].id == config.guild_id
            and ctx["message"].channel.id not in config.karma_banned_channels
            and config.karma_ban_role_id not in map(lambda x: x.id, ctx["member"].roles)
        ):
            if isinstance(ctx["emoji"], str):
                karma_r.karma_emoji_remove(ctx["message"].author, ctx["member"], ctx["emoji"])
            else:
                karma_r.karma_emoji_remove(ctx["message"].author, ctx["member"], ctx["emoji"].id)

    @commands.cooldown(rate=5, per=30.0, type=commands.BucketType.user)
    @commands.group(pass_context=True)
    async def karma(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            args = ctx.message.content.split()[1:]

            if len(args) == 0:
                await ctx.send(self.karma.karma_get(ctx.author))
                await self.check.botroom_check(ctx.message)
            else:
                await ctx.send(utils.fill_message("karma_invalid_command", user=ctx.author.id))

    @karma.command()
    async def stalk(self, ctx, *args):
        try:
            converter = commands.MemberConverter()
            target_member = await converter.convert(ctx=ctx, argument=" ".join(args))
        except commands.errors.BadArgument:
            await ctx.send(utils.fill_message("member_not_found", user=ctx.author.id))
            return

        await ctx.send(self.karma.karma_get(ctx.author, target_member))
        await self.check.botroom_check(ctx.message)

    @karma.command()
    @commands.cooldown(rate=2, per=30.0, type=commands.BucketType.user)
    async def get(self, ctx, *args):
        if not await self.check.guild_check(ctx.message):
            await ctx.send(messages.server_warning)
        else:
            try:
                await self.karma.emoji_get_value(ctx.message)
                await self.check.botroom_check(ctx.message)
            except discord.errors.Forbidden:
                return

    @karma.command()
    @commands.check(utils.is_bot_admin)
    async def revote(self, ctx, *args):
        if not await self.check.guild_check(ctx.message):
            await ctx.send(messages.server_warning)
        else:
            if ctx.message.channel.id == config.vote_room:
                try:
                    await ctx.message.delete()
                    await self.karma.emoji_revote_value(ctx.message)
                except discord.errors.Forbidden:
                    return
            else:
                dc_vote_room = discord.utils.get(ctx.guild.channels, id=config.vote_room)
                await ctx.send(utils.fill_message("vote_room_only", room=dc_vote_room))

    @karma.command()
    @commands.check(utils.is_bot_admin)
    async def vote(self, ctx, *args):
        if not await self.check.guild_check(ctx.message):
            await ctx.send(messages.server_warning)
        else:
            if ctx.message.channel.id == config.vote_room:
                try:
                    await ctx.message.delete()
                    await self.karma.emoji_vote_value(ctx.message)
                except discord.errors.Forbidden:
                    return
            else:
                dc_vote_room = discord.utils.get(ctx.guild.channels, id=config.vote_room)
                await ctx.send(utils.fill_message("vote_room_only", room=dc_vote_room))

    @karma.command()
    @commands.check(utils.is_bot_admin)
    async def give(self, ctx, *args):
        await self.karma.karma_give(ctx.message)

    @karma.command()
    async def message(self, ctx, *args):
        async with ctx.channel.typing():
            try:
                converter = commands.MessageConverter()
                target_message = await converter.convert(ctx=ctx, argument=" ".join(args))
            except commands.errors.BadArgument:
                await ctx.send(utils.fill_message("karma_message_format", user=ctx.author.id))
                return
            await self.karma.message_karma(ctx, target_message)

    @karma.command()
    @commands.check(utils.is_bot_admin)
    async def transfer(self, ctx, *args):
        await self.karma.karma_transfer(ctx.message)

    @commands.cooldown(rate=2, per=30.0, type=commands.BucketType.user)
    @commands.command()
    async def leaderboard(self, ctx, start=1):
        if not await self.validate_leaderboard_offset(start, ctx):
            return

        await self.karma.leaderboard(ctx, "get", "DESC", start)
        await self.check.botroom_check(ctx.message)

    @commands.cooldown(rate=2, per=30.0, type=commands.BucketType.user)
    @commands.command()
    async def bajkarboard(self, ctx, start=1):
        if not await self.validate_leaderboard_offset(start, ctx):
            return

        await self.karma.leaderboard(ctx, "get", "ASC", start)
        await self.check.botroom_check(ctx.message)

    @commands.cooldown(rate=2, per=30.0, type=commands.BucketType.user)
    @commands.command()
    async def givingboard(self, ctx, start=1):
        if not await self.validate_leaderboard_offset(start, ctx):
            return

        await self.karma.leaderboard(ctx, "give", "DESC", start)
        await self.check.botroom_check(ctx.message)

    @commands.cooldown(rate=2, per=30.0, type=commands.BucketType.user)
    @commands.command()
    async def ishaboard(self, ctx, start=1):
        if not await self.validate_leaderboard_offset(start, ctx):
            return

        await self.karma.leaderboard(ctx, "give", "ASC", start)
        await self.check.botroom_check(ctx.message)

    @leaderboard.error
    @bajkarboard.error
    @givingboard.error
    @ishaboard.error
    async def leaderboard_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(utils.fill_message("karma_lederboard_offser_error", user=ctx.author.id))

    @revote.error
    @vote.error
    @give.error
    @transfer.error
    async def karma_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send(utils.fill_message("insufficient_rights", user=ctx.author.id))

    async def validate_leaderboard_offset(self, offset: int, ctx: commands.Context) -> bool:
        if not 0 < offset < 100000000:  # Any value larger than the server
            # user cnt and lower than 32bit
            # int max will do
            await ctx.send(utils.fill_message("karma_lederboard_offser_error", user=ctx.author.id))
            return False

        return True


def setup(bot):
    bot.add_cog(Karma(bot))
