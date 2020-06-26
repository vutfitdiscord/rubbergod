from cogs.base_cog import BaseCog
import discord
from discord.ext import commands

import utils
from config import app_config as config, messages
from features import karma, reaction
from repository import karma_repo
from cogs import room_check


karma_r = karma_repo.KarmaRepository()
config = config.Config
messages = messages.Messages


class Karma(BaseCog):

    def __init__(self, bot):
        super().__init__(bot)
        self.karma = karma.Karma(bot, karma_r)
        self.check = room_check.RoomCheck(bot)
        self.reaction = reaction.Reaction(bot, karma_r)

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author.bot:
            return

        if message.content.startswith(config.role_string) or\
           message.channel.id in config.role_channels:
            role_data = await self.reaction.get_join_role_data(message)
            await self.reaction.message_role_reactions(message, role_data)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        try:
            await self.reaction.add(payload)
        except discord.HTTPException:
            # ignore HTTP Exceptions
            return

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        try:
            await self.reaction.remove(payload)
        except discord.HTTPException:
            # ignore HTTP Exceptions
            return

    @commands.cooldown(rate=5, per=30.0, type=commands.BucketType.user)
    @commands.command(name="karma")
    async def pick_karma_command(self, ctx, *args):
        karma = self.karma
        if len(args) == 0:
            await ctx.send(karma.karma_get(ctx.author))
            await self.check.botroom_check(ctx.message)

        elif args[0] == "stalk":
            try:
                converter = commands.MemberConverter()
                target_member = await converter.convert(
                    ctx=ctx, argument=' '.join(args[1:]))
            except commands.errors.BadArgument:
                await ctx.send(utils.fill_message("member_not_found", user=ctx.author.id))
                return

            await ctx.send(karma.karma_get(ctx.author, target_member))
            await self.check.botroom_check(ctx.message)

        elif args[0] == "get":
            if not await self.check.guild_check(ctx.message):
                await ctx.send(messages.server_warning)
            else:
                try:
                    await karma.emoji_get_value(ctx.message)
                    await self.check.botroom_check(ctx.message)
                except discord.errors.Forbidden:
                    return

        elif args[0] == "revote":
            if not await self.check.guild_check(ctx.message):
                await ctx.send(messages.server_warning)
            else:
                if ctx.message.channel.id == config.vote_room or \
                   ctx.author.id == config.admin_id:
                    try:
                        await ctx.message.delete()
                        await karma.emoji_revote_value(ctx.message)
                    except discord.errors.Forbidden:
                        return
                else:
                    dc_vote_room = discord.utils.get(ctx.guild.channels, id=config.vote_room)
                    await ctx.send(utils.fill_message("vote_room_only", room=dc_vote_room))

        elif args[0] == "vote":
            if not await self.check.guild_check(ctx.message):
                await ctx.send(messages.server_warning)
            else:
                if ctx.message.channel.id == config.vote_room or \
                   ctx.author.id == config.admin_id:
                    try:
                        await ctx.message.delete()
                        await karma.emoji_vote_value(ctx.message)
                    except discord.errors.Forbidden:
                        return
                else:
                    dc_vote_room = discord.utils.get(ctx.guild.channels, id=config.vote_room)
                    await ctx.send(utils.fill_message("vote_room_only", room=dc_vote_room))

        elif args[0] == "give":
            if not await self.validate_admin_rights(ctx):
                return

            await karma.karma_give(ctx.message)

        elif args[0] == "message":
            try:
                converter = commands.MessageConverter()
                target_message = await converter.convert(
                    ctx=ctx, argument=' '.join(args[1:]))
            except commands.errors.BadArgument:
                await ctx.send(utils.fill_message("karma_message_format", user=ctx.author.id))
                return
            await karma.message_karma(ctx, target_message)
        elif args[0] == "transfer":
            if not await self.validate_admin_rights(ctx):
                return

            await karma.karma_transfer(ctx.message)
        else:
            await ctx.send(utils.fill_message("karma_invalid_command", user=ctx.author.id))

    @commands.cooldown(rate=2, per=30.0, type=commands.BucketType.user)
    @commands.command()
    async def leaderboard(self, ctx, start=1):
        if not self.validate_leaderboard_offset(start):
            return

        await self.karma.leaderboard(ctx.message.channel, 'get', 'DESC', start)
        await self.check.botroom_check(ctx.message)

    @commands.cooldown(rate=2, per=30.0, type=commands.BucketType.user)
    @commands.command()
    async def bajkarboard(self, ctx, start=1):
        if not self.validate_leaderboard_offset(start):
            return

        await self.karma.leaderboard(ctx.message.channel, 'get', 'ASC', start)
        await self.check.botroom_check(ctx.message)

    @commands.cooldown(rate=2, per=30.0, type=commands.BucketType.user)
    @commands.command()
    async def givingboard(self, ctx, start=1):
        if not self.validate_leaderboard_offset(start):
            return

        await self.karma.leaderboard(ctx.message.channel, 'give', 'DESC', start)
        await self.check.botroom_check(ctx.message)

    @commands.cooldown(rate=2, per=30.0, type=commands.BucketType.user)
    @commands.command()
    async def ishaboard(self, ctx, start=1):
        if not self.validate_leaderboard_offset(start):
            return

        await self.karma.leaderboard(ctx.message.channel, 'give', 'ASC', start)
        await self.check.botroom_check(ctx.message)

    @leaderboard.error
    @bajkarboard.error
    @givingboard.error
    @ishaboard.error
    async def leaderboard_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(utils.fill_message("karma_lederboard_offser_error", user=ctx.author.id))

    async def validate_leaderboard_offset(self, offset: int, ctx: commands.Context) -> bool:
        if (not 0 < offset < 100000000):  # Any value larger than the server
            # user cnt and lower than 32bit
            # int max will do
            await ctx.send(utils.fill_message("karma_lederboard_offser_error", user=ctx.author.id))
            return False

        return True


def setup(bot):
    bot.add_cog(Karma(bot))
