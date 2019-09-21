from datetime import datetime

import typing

from discord import Reaction, Member, User, RawReactionActionEvent
from discord.ext import commands
from discord.ext.commands import BadArgument

from config.config import Config
from features import vote


class DateTimeConverter(commands.Converter):
    async def convert(self, ctx, argument):
        ret = vote.Vote.parse_vote_date(argument)
        if ret is None:
            raise BadArgument()
        return ret


class Vote(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voter = vote.Vote(bot)
        self.handled = []

    @commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)
    @commands.command(rest_is_raw=True)
    async def vote(self, ctx, date: typing.Optional[DateTimeConverter], *, message):
        await self.voter.handle_vote(ctx, date, message)

    def __handle(self, msg_id, user_id, emoji, add, raw):
        t = (msg_id, user_id,)

        if t in self.handled:
            self.handled.remove(t)
            return True

        if not raw:
            self.handled.append(t)
        return False

    async def handle_raw_reaction(self, payload: RawReactionActionEvent, added: bool):
        chan = await self.bot.fetch_channel(payload.channel_id)
        msg = await chan.fetch_message(payload.message_id)
        usr = await self.bot.fetch_user(payload.user_id)

        for r in msg.reactions:
            if str(r.emoji) == str(payload.emoji):
                await self.voter.handle_reaction(r, usr, added)
                return True

        return False

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: Reaction, user):
        if self.__handle(reaction.message.id, user.id, reaction.emoji, True, False):
            # print("Already handled")
            return

        # print("Handling")
        await self.voter.handle_reaction(reaction, user, True)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        if self.__handle(payload.message_id, payload.user_id, payload.emoji, True, True):
            # print("Already handled (in RAW)")
            return

        # print("Handling RAW")
        if not await self.handle_raw_reaction(payload, True):
            print("Couldn't find reaction, that is rather weird.")

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction: Reaction, user):
        if self.__handle(reaction.message.id, user.id, reaction.emoji, False, False):
            # print("Already handled")
            return

        # print("Handling")
        await self.voter.handle_reaction(reaction, user, False)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: RawReactionActionEvent):
        if self.__handle(payload.message_id, payload.user_id, payload.emoji, False, True):
            # print("Already handled (in RAW)")
            return

        # print("Handling RAW")
        if not await self.handle_raw_reaction(payload, False):
            print("Couldn't find reaction, that is rather weird.")


def setup(bot):
    bot.add_cog(Vote(bot))
