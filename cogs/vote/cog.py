"""
Cog implementing vote and polls feature.
"""

import asyncio
import re
from datetime import datetime

from disnake import Message, RawReactionActionEvent, TextChannel
from disnake.errors import NotFound
from disnake.ext import commands

import utils
from cogs.base import Base
from config import cooldowns
from database.vote import VoteDB
from utils import str_emoji_id

from .features import VoteMessage
from .messages_cz import MessagesCZ


class Vote(Base, commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
        self.vote_cache: dict[int, VoteMessage] = {}

    async def load_cached(self):
        db_votes = VoteDB.get_pending_votes()
        for v in db_votes:
            try:
                chan = await utils.get_or_fetch_channel(self.bot, v.channel_id)
                msg = await chan.fetch_message(v.message_id)
                self.vote_cache[v.message_id] = VoteMessage(msg.content, v.is_one_of)
                await self.init_vote(msg)
            except (VoteMessage.ParseError, VoteMessage.NotEmojiError, NotFound):
                pass

    @cooldowns.short_cooldown
    @commands.command(rest_is_raw=True, description=MessagesCZ.vote_format, brief=MessagesCZ.vote_brief)
    async def vote(self, ctx, *, message):
        await self.handle_vote_command(ctx, message, False)

    @cooldowns.short_cooldown
    @commands.command(
        rest_is_raw=True,
        name="singlevote",
        description=MessagesCZ.vote_format,
        brief=MessagesCZ.singlevote_brief,
    )
    async def vote_one_of(self, ctx: commands.Context, *, message: str):
        await self.handle_vote_command(ctx, message, True)

    async def handle_vote_command(self, ctx: commands.Context, message: str, one_of: bool):
        if len(message.strip()) == 0:
            await ctx.send(MessagesCZ.vote_format)
            return
        try:
            parsed_vote = VoteMessage(message, one_of)
        except VoteMessage.ParseError:
            await ctx.send(MessagesCZ.bad_format)
            return
        except VoteMessage.NotEmojiError as e:
            await ctx.send(MessagesCZ.not_emoji(opt=str(e)))
            return

        if parsed_vote.end_date is not None and parsed_vote.end_date < datetime.now():
            await ctx.send(MessagesCZ.bad_date)
            return

        self.vote_cache[ctx.message.id] = parsed_vote
        VoteDB.add_vote(ctx.message.id, ctx.channel.id, parsed_vote.end_date, one_of)
        ret = await self.init_vote(ctx.message)
        if ret:
            # init_failed: remove vote from DB and cache
            VoteDB.remove(ctx.message.id)
            del self.vote_cache[ctx.message.id]
            match = re.search(f"<:(.*):{ret}>", message)
            await ctx.send(MessagesCZ.emote_not_found(emote=match.group(1)))
        else:
            await ctx.send(MessagesCZ.vote_none)

    async def init_vote(self, message: Message):
        vote = self.vote_cache[message.id]
        handled_opts = []
        for msg_reaction in message.reactions:
            r_id = str_emoji_id(msg_reaction.emoji)
            if r_id in vote.options:
                vote.options[r_id].count = msg_reaction.count - 1
                handled_opts.append(r_id)
            else:
                async for u in msg_reaction.users():
                    await msg_reaction.remove(u)

        for opt in vote.options:
            if opt not in handled_opts:
                if vote.options[opt].is_unicode:
                    e = vote.options[opt].emoji
                else:
                    e = self.bot.get_emoji(int(vote.options[opt].emoji))
                if e is None:
                    return vote.options[opt].emoji
                await message.add_reaction(e)

        if vote.end_date is not None:
            sec = (vote.end_date - datetime.now()).total_seconds()
            if sec < 1:
                sec = 1
            asyncio.ensure_future(self.send_final_message(sec, message.id, message.channel.id))
        return 0

    async def handle_raw_reaction_add(self, payload: RawReactionActionEvent):
        # Called from reactions.py
        if payload.message_id not in self.vote_cache:
            return

        vote = self.vote_cache[payload.message_id]
        chan = await utils.get_or_fetch_channel(self.bot, payload.channel_id)

        emoji_str = str_emoji_id(payload.emoji)

        if emoji_str not in vote.options:
            msg = await chan.fetch_message(payload.message_id)
            usr = await self.bot.get_or_fetch_user(payload.user_id)
            await msg.remove_reaction(payload.emoji, usr)
            return

        if vote.is_one_of:
            msg: Message = await chan.fetch_message(payload.message_id)
            usr = await self.bot.get_or_fetch_user(payload.user_id)
            for r in msg.reactions:
                if str_emoji_id(r.emoji) == emoji_str:
                    continue

                if await r.users().find(lambda x: x.id == usr.id):
                    # Increment the counter here, so that on_raw_reaction_remove can decrement it again
                    vote.options[emoji_str].count += 1
                    await msg.remove_reaction(payload.emoji, usr)
                    return

        last_max_opt = max(vote.options.values(), key=lambda x: x.count).count

        vote.options[emoji_str].count += 1
        if vote.options[emoji_str].count >= last_max_opt:
            msg = await chan.fetch_message(payload.message_id)
            await self.update_bot_vote_message(msg, chan)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: RawReactionActionEvent):
        if payload.message_id not in self.vote_cache:
            return

        vote = self.vote_cache[payload.message_id]
        if str_emoji_id(payload.emoji) not in vote.options:
            return

        chan = await utils.get_or_fetch_channel(self.bot, payload.channel_id)
        emoji_str = str_emoji_id(payload.emoji)

        last_max_opt = max(vote.options.values(), key=lambda x: x.count).count

        vote.options[emoji_str].count -= 1
        if (vote.options[emoji_str].count + 1) == last_max_opt:
            msg = await chan.fetch_message(payload.message_id)
            await self.update_bot_vote_message(msg, chan)

    @commands.Cog.listener()
    async def on_ready(self):
        await self.load_cached()

    def get_message(self, vote: VoteMessage, final: bool):
        def singularise(msg: str):
            return msg.replace(" 1 hlasy.", " 1 hlasem.")

        most_voted = max(vote.options.values(), key=lambda x: x.count).count
        all_most_voted = list(filter(lambda x: x.count == most_voted, vote.options.values()))

        if most_voted <= 0:
            return MessagesCZ.result_none if final else MessagesCZ.vote_none

        if len(all_most_voted) == 1:
            option = all_most_voted[0]

            if final:
                return singularise(
                    MessagesCZ.vote_result(
                        winning_emoji=(
                            option.emoji if option.is_unicode else str(self.bot.get_emoji(int(option.emoji)))
                        ),
                        winning_option=option.message,
                        votes=option.count,
                        question=vote.question,
                    )
                )
            else:
                return singularise(
                    MessagesCZ.vote_winning(
                        winning_emoji=(
                            option.emoji if option.is_unicode else str(self.bot.get_emoji(int(option.emoji)))
                        ),
                        winning_option=option.message,
                        votes=option.count,
                    )
                )
        else:
            emoji_str = ""
            for e in all_most_voted:
                emoji_str += (e.emoji if e.is_unicode else str(self.bot.get_emoji(int(e.emoji)))) + ", "
            emoji_str = emoji_str[:-2]

            if final:
                return singularise(
                    MessagesCZ.result_multiple(
                        winning_emojis=emoji_str, votes=most_voted, question=vote.question
                    )
                )
            else:
                return singularise(MessagesCZ.winning_multiple(winning_emojis=emoji_str, votes=most_voted))

    async def update_bot_vote_message(self, vote_msg: Message, channel: TextChannel):
        vote = self.vote_cache[vote_msg.id]
        bot_msg = await channel.history(limit=3, after=vote_msg.created_at).get(author__id=self.bot.user.id)

        if bot_msg is None:
            return

        await bot_msg.edit(content=self.get_message(vote, False))

    async def send_final_message(self, timeout: int, message_id: int, channel_id: int):
        await asyncio.sleep(timeout)
        vote = self.vote_cache[message_id]
        chan = await utils.get_or_fetch_channel(self.bot, channel_id)
        await chan.send(content=self.get_message(vote, True))
        VoteDB.remove(message_id)
