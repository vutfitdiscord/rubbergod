import discord
from discord.ext import commands

import utils
from utils import fill_message
from config import messages, config
from features import karma, reaction
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
        await self.reaction.add(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        await self.reaction.remove(payload)

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
                await ctx.send(fill_message("member_not_found", user=ctx.author.id))
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
                await ctx.send(
                    "{}".format(messages.server_warning))
            else:
                if ctx.message.channel.id == config.vote_room or \
                   ctx.author.id == config.admin_id:
                    try:
                        await ctx.message.delete()
                        await karma.emoji_revote_value(ctx.message)
                    except discord.errors.Forbidden:
                        return
                else:
                    await ctx.send(
                        messages.vote_room_only
                        .format(room=discord.utils.get(ctx.guild.channels,
                                                       id=config.vote_room)))

        elif args[0] == "vote":
            if not await self.check.guild_check(ctx.message):
                await ctx.send(
                    "{}".format(messages.server_warning))
            else:
                if ctx.message.channel.id == config.vote_room or \
                   ctx.author.id == config.admin_id:
                    try:
                        await ctx.message.delete()
                        await karma.emoji_vote_value(ctx.message)
                    except discord.errors.Forbidden:
                        return
                else:
                    await ctx.send(
                        messages.vote_room_only
                        .format(room=discord.utils.get(ctx.guild.channels,
                                                       id=config.vote_room)))

        elif args[0] == "give":
            if ctx.author.id == config.admin_id:
                await karma.karma_give(ctx.message)
            else:
                await ctx.send(fill_message("insufficient_rights", user=ctx.author.id))
        else:
            await ctx.send(fill_message("karma_invalid_command", user=ctx.author.id))

    @commands.cooldown(rate=2, per=30.0, type=commands.BucketType.user)
    @commands.command()
    async def leaderboard(self, ctx, start=1):
        if (not 0 < start < 100000000): # Any value larger than the server
                                        # user cnt and lower than 32bit
                                        # int max will do
            await ctx.send(fill_message("karma_lederboard_offser_error", user=ctx.author.id))
            return
        await self.karma.leaderboard(ctx.message.channel, 'get', 'DESC', start)
        await self.check.botroom_check(ctx.message)

    @commands.cooldown(rate=2, per=30.0, type=commands.BucketType.user)
    @commands.command()
    async def bajkarboard(self, ctx, start=1):
        if (not 0 < start < 100000000): # Any value larger than the server
                                        # user cnt and lower than 32bit
                                        # int max will do
            await ctx.send(fill_message("karma_lederboard_offser_error", user=ctx.author.id))
            return
        await self.karma.leaderboard(ctx.message.channel, 'get', 'ASC', start)
        await self.check.botroom_check(ctx.message)

    @commands.cooldown(rate=2, per=30.0, type=commands.BucketType.user)
    @commands.command()
    async def givingboard(self, ctx, start=1):
        if (not 0 < start < 100000000): # Any value larger than the server
                                        # user cnt and lower than 32bit
                                        # int max will do
            await ctx.send(fill_message("karma_lederboard_offser_error", user=ctx.author.id))
            return
        await self.karma.leaderboard(ctx.message.channel, 'give', 'DESC', start)
        await self.check.botroom_check(ctx.message)

    @commands.cooldown(rate=2, per=30.0, type=commands.BucketType.user)
    @commands.command()
    async def ishaboard(self, ctx, start=1):
        if (not 0 < start < 100000000): # Any value larger than the server
                                        # user cnt and lower than 32bit
                                        # int max will do
            await ctx.send(fill_message("karma_lederboard_offser_error", user=ctx.author.id))
            return
        await self.karma.leaderboard(ctx.message.channel, 'give', 'ASC', start)
        await self.check.botroom_check(ctx.message)

    @leaderboard.error
    @bajkarboard.error
    @givingboard.error
    @ishaboard.error
    async def leaderboard_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(fill_message("karma_lederboard_offser_error", user=ctx.author.id))


def setup(bot):
    bot.add_cog(Karma(bot))
