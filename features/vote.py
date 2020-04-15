import asyncio
from datetime import datetime

import discord
from discord import HTTPException, Reaction, User, Message
from discord.ext.commands import Bot, Context

from config import messages
from features.base_feature import BaseFeature

import utils

class MessageData:
    def __init__(self, question, options, date: datetime = None):
        self.question = question
        self.options = options
        self.date = date

    def is_valid(self):
        return self.question is not None and self.options is not None \
               and len(self.question) != 0 and len(self.options) != 0


class Vote(BaseFeature):
    def __init__(self, bot: Bot):
        super().__init__(bot)

    # There might be a better way to do this.
    @staticmethod
    def parse_vote_date(arg1, arg2, def_date: datetime):
        def parse_date(a):
            try:
                dt = datetime.strptime(a, "%d.%m.%y")
                return dt
            except ValueError:
                try:
                    dt = datetime.strptime(a, "%d.%m.")
                    dt = dt.replace(year=def_date.year)
                    return dt
                except ValueError:
                    return None

        def parse_time(a):
            try:
                dt = datetime.strptime(a, "%H:%M")
                dt = dt.replace(year=def_date.year, month=def_date.month,
                                day=def_date.day)
                return dt
            except ValueError:
                return None

        date = parse_date(arg1)
        if date is None:
            time = parse_time(arg1)
            if time is None:
                return None
            return time, 1
        else:
            time = parse_time(arg2)
            if time is None:
                return date, 1
            return datetime.combine(date.date(), time.time()), 2

    async def get_message_data_raw(self, target_msg: Message):
        msg = target_msg.content
        msg_split = msg.split()

        if len(msg_split) < 2:
            return None

        vote_par = 0
        if msg_split[0][1:] == "vote":
            vote_par = 0
        elif msg_split[1] == "vote":
            vote_par = 1
        else:
            return None

        d = self.parse_vote_date(msg_split[vote_par + 1],
                                 msg_split[vote_par + 2],
                                 target_msg.created_at)

        lines = msg.splitlines()
        if len(lines) < 2:
            return None

        try:
            if d is None:
                question = lines[0][(lines[0].index("vote ") + 5):]
            else:
                question = " ".join(
                    lines[0][(lines[0].index("vote ") + 5):].split()[d[1]:])

            options_raw = [(x[:x.index(" ")].strip(), x[x.index(" "):].strip()) for
                           x in lines[1:]]
        except ValueError:
            return None

        return MessageData(question, options_raw, None if d is None else d[0])

    async def get_message_data(self, msg: str):
        lines = msg.splitlines()
        if len(lines) < 2:
            return None

        question = lines[0]
        options_raw = [(x[:x.index(" ")].strip(), x[x.index(" "):].strip()) for
                       x in lines[1:]]

        return MessageData(question, options_raw)

    async def handle_vote(self, context: Context, date: datetime,
                          time: datetime, message: str):
        data = await self.get_message_data(message)

        if data is None or not data.is_valid():
            await context.message.channel.send(messages.Messages.vote_format)
            return

        if date is None:
            data.date = time
        else:
            if time is None:
                data.date = date
            else:
                data.date = datetime.combine(date.date(), time.time())

        if data.date is not None and data.date < datetime.now():
            await context.message.channel.send(messages.Messages.vote_bad_date)
            return

        for o in data.options:
            try:
                await context.message.add_reaction(o[0])
            except HTTPException:
                await context.message.channel.send(
                    messages.Messages.vote_not_emoji
                                     .format(not_emoji=o[0]))

        await context.message.channel.send(messages.Messages.vote_none)

        if data.date is not None:
            sec = (data.date - datetime.now()).total_seconds()
            asyncio.ensure_future(
                self.send_winning_msg(context.channel.id, context.message.id,
                                      sec))

    @staticmethod
    def singularise(msg: str):
        return msg.replace("1 hlasy.", "1 hlasem.")

    async def send_winning_msg(self, channel_id, vote_msg_id, timeout):
        await asyncio.sleep(timeout)
        chan = await self.bot.fetch_channel(channel_id)
        target_msg = await chan.fetch_message(vote_msg_id)
        data = await self.get_message_data_raw(target_msg)

        if data is None:
            return

        r = [x for x in target_msg.reactions if
             any(str(x.emoji) == a[0] for a in data.options)]

        most_voted = max(r, key=lambda x: x.count)
        all_most_voted = list(filter(lambda x: x.count == most_voted.count, r))

        if most_voted.count == 1:
            await chan.send(content=messages.Messages.vote_result_none
                            .format(question=data.question))
            return

        if len(all_most_voted) == 1:
            option = \
                [a[1] for a in data.options if str(most_voted.emoji) == a[0]][
                    0]

            await chan.send(
                content=self.singularise(utils.fill_message(
                    "vote_result",
                    question=discord.utils.escape_mentions(data.question),
                    winning_emoji=most_voted.emoji,
                    winning_option=discord.utils.escape_mentions(option),
                    votes=(most_voted.count - 1)
                ))
            )
        else:
            emoji_str = ""
            for e in all_most_voted:
                emoji_str += str(e.emoji) + ", "
            emoji_str = emoji_str[:-2]
            await chan.send(
                content=self.singularise(
                    utils.fill_message(
                        "vote_result_multiple",
                        question=discord.utils.escape_mentions(data.question),
                        winning_emojis=emoji_str,
                        votes=(most_voted.count - 1)
                    )
                )
            )

    # The lookups in this method are ineffective.
    # We could definitely get rid of all the iterations.
    async def handle_reaction(self, reaction: Reaction, user: User,
                              added: bool):
        target_msg = reaction.message
        data = await self.get_message_data_raw(target_msg)

        if data is None or not data.is_valid():
            return

        if data.date is not None and data.date < datetime.now():
            if added:
                await reaction.message.remove_reaction(reaction.emoji, user)
            return

        if not any(str(reaction.emoji) == a[0] for a in data.options):
            if added:
                await reaction.message.remove_reaction(reaction.emoji, user)
            return
        else:
            if added and not any(a.me and a.emoji == reaction.emoji for a in
                                 target_msg.reactions):
                await target_msg.add_reaction(reaction.emoji)

        bot_msg = await target_msg.channel.history(
            limit=3,
            after=target_msg.created_at
        ).get(author__id=self.bot.user.id)

        if bot_msg is None:
            return

        r = [x for x in target_msg.reactions if
             any(str(x.emoji) == a[0] for a in data.options)]

        most_voted = max(r, key=lambda x: x.count)
        all_most_voted = list(filter(lambda x: x.count == most_voted.count, r))

        if most_voted.count == 1:
            await bot_msg.edit(content=messages.Messages.vote_none)
            return

        if len(all_most_voted) == 1:
            option = \
                [a[1] for a in data.options if str(most_voted.emoji) == a[0]][
                    0]

            await bot_msg.edit(
                content=self.singularise(utils.fill_message(
                    "vote_winning",
                    winning_emoji=most_voted.emoji,
                    winning_option=option,
                    votes=(most_voted.count - 1)
                )))
        else:
            emoji_str = ""
            for e in all_most_voted:
                emoji_str += str(e.emoji) + ", "
            emoji_str = emoji_str[:-2]
            await bot_msg.edit(
                content=self.singularise(
                    utils.fill_message(
                        "vote_winning_multiple",
                        winning_emojis=emoji_str,
                        votes=(most_voted.count - 1)
                    )
                )
            )
