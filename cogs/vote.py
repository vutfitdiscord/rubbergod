"""
Cog implementing vote and polls feature.
"""

import asyncio
import re
from datetime import datetime
from typing import Dict

import emoji
from dateutil import parser
from disnake import Message, RawReactionActionEvent, TextChannel
from disnake.errors import NotFound
from disnake.ext import commands
from disnake.ext.commands import Bot, Context

import utils
from cogs.base import Base
from config import cooldowns
from config.messages import Messages
from database.vote import VoteDB
from utils import is_command_message, str_emoji_id


class VoteMessage:
    class VoteOption:
        def __init__(self, emoji: str, is_unicode: bool, message: str, count: int):
            self.emoji = emoji
            self.message = message
            self.count = count
            self.is_unicode = is_unicode

    class ParseError(Exception):
        pass

    class NotEmojiError(Exception):
        pass

    emoji_regex = re.compile('^<:.*:([0-9]+)>(.+)')

    @classmethod
    def parse_option(cls, opt_line: str) -> VoteOption:
        matches = cls.emoji_regex.match(opt_line)
        if matches is None:
            # it is not a disnake emoji, try unicode
            emojis = emoji.emoji_list(opt_line)
            if len(emojis) > 0 and emojis[0]['match_start'] == 0:
                opt_emoji = emojis[0]['emoji']
                opt_message = opt_line[len(opt_emoji):].strip()
            else:
                raise cls.NotEmojiError(opt_line)
        else:
            opt_emoji = matches.group(1)
            opt_message = matches.group(2).strip()

        return cls.VoteOption(opt_emoji, matches is None, opt_message, 0)

    def __init__(self, message: str, is_one_of: bool):
        self.is_one_of = is_one_of
        if is_command_message('vote', message) or is_command_message('singlevote', message):
            message = message[(message.index('vote') + 4):]

        # If date/time line is present:
        # line 1: date
        # line 2: question
        # lines 3,4..n: emoji option
        if len(message.strip()) == 0:
            raise self.ParseError()
        lines = message.splitlines(False)
        if len(lines) < 3:
            raise self.ParseError()

        try:
            self.end_date = parser.parse(lines[0], dayfirst=True, fuzzy=True)
            lines = lines[1:]  # Only keep lines with the question and the options
        except parser.ParserError:
            self.end_date = None
            # The user might have actually followed the help and put a newline before the question
            if len(lines[0].strip()) == 0:
                lines = lines[1:]

        if len(lines) < 3:  # Do we still have at least the question and two options?
            raise self.ParseError()

        self.question = lines[0]
        parsed_opts = [self.parse_option(x.strip()) for x in lines[1:]]
        self.options: Dict[str, 'VoteMessage.VoteOption'] = {x.emoji: x for x in parsed_opts}
        # Check if emojis are unique
        if len(self.options) != len(set(self.options.keys())):
            raise self.ParseError()


class Vote(Base, commands.Cog):
    def __init__(self, bot: Bot):
        super().__init__()
        self.bot = bot
        self.vote_cache: Dict[int, VoteMessage] = {}

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
    @commands.command(rest_is_raw=True, description=Messages.vote_format, brief=Messages.vote_brief)
    async def vote(self, ctx, *, message):
        await self.handle_vote_command(ctx, message, False)

    @cooldowns.short_cooldown
    @commands.command(rest_is_raw=True, name='singlevote', description=Messages.vote_format,
                      brief=Messages.vote_one_of_brief)
    async def vote_one_of(self, ctx, *, message):
        await self.handle_vote_command(ctx, message, True)

    async def handle_vote_command(self, ctx: Context, message: str, one_of: bool):
        if len(message.strip()) == 0:
            await ctx.send(Messages.vote_format)
            return
        try:
            parsed_vote = VoteMessage(message, one_of)
        except VoteMessage.ParseError:
            await ctx.send(Messages.vote_bad_format)
            return
        except VoteMessage.NotEmojiError as e:
            await ctx.send(Messages.vote_not_emoji(opt=str(e)))
            return

        if parsed_vote.end_date is not None and parsed_vote.end_date < datetime.now():
            await ctx.send(Messages.vote_bad_date)
            return

        self.vote_cache[ctx.message.id] = parsed_vote
        VoteDB.add_vote(ctx.message.id, ctx.channel.id, parsed_vote.end_date, one_of)
        ret = await self.init_vote(ctx.message)
        if ret:
            # init_failed: remove vote from DB and cache
            VoteDB.remove(ctx.message.id)
            del self.vote_cache[ctx.message.id]
            match = re.search(f"<:(.*):{ret}>", message)
            await ctx.send(Messages.emote_not_found(emote=match.group(1)))
        else:
            await ctx.send(Messages.vote_none)

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
            return Messages.vote_result_none if final else Messages.vote_none

        if len(all_most_voted) == 1:
            option = all_most_voted[0]

            if final:
                return singularise(Messages.vote_result(
                    winning_emoji=(
                        option.emoji if option.is_unicode else str(self.bot.get_emoji(int(option.emoji)))
                    ),
                    winning_option=option.message,
                    votes=option.count,
                    question=vote.question))
            else:
                return singularise(Messages.vote_winning(
                    winning_emoji=(
                        option.emoji if option.is_unicode else str(self.bot.get_emoji(int(option.emoji)))
                    ),
                    winning_option=option.message,
                    votes=option.count))
        else:
            emoji_str = ""
            for e in all_most_voted:
                emoji_str += (e.emoji if e.is_unicode else str(self.bot.get_emoji(int(e.emoji)))) + ", "
            emoji_str = emoji_str[:-2]

            if final:
                return singularise(Messages.vote_result_multiple(
                    winning_emojis=emoji_str,
                    votes=most_voted,
                    question=vote.question
                ))
            else:
                return singularise(Messages.vote_winning_multiple(
                    winning_emojis=emoji_str,
                    votes=most_voted
                ))

    async def update_bot_vote_message(self, vote_msg: Message, channel: TextChannel):
        vote = self.vote_cache[vote_msg.id]
        bot_msg = await channel.history(
            limit=3,
            after=vote_msg.created_at
        ).get(author__id=self.bot.user.id)

        if bot_msg is None:
            return

        await bot_msg.edit(content=self.get_message(vote, False))

    async def send_final_message(self, timeout, message_id, channel_id):
        await asyncio.sleep(timeout)
        vote = self.vote_cache[message_id]
        chan = await utils.get_or_fetch_channel(self.bot, channel_id)
        await chan.send(content=self.get_message(vote, True))
        VoteDB.remove(message_id)


def setup(bot):
    bot.add_cog(Vote(bot))
