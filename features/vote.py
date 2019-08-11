from discord import Message, HTTPException, PartialEmoji
from discord.ext.commands import Bot, Context

from config import config, messages
from features.base_feature import BaseFeature


class MessageData:
    def __init__(self, question, options):
        self.question = question
        self.options = options


class Vote(BaseFeature):
    def __init__(self, bot: Bot):
        super().__init__(bot)

    async def get_message_data(self, message: Message):
        msg = message.content

        if len(msg.split()) < 2:
            return None

        if msg[1:].startswith("vote") and msg[0] in config.Config.command_prefix:
            lines = msg.splitlines()
            question = lines[0][(lines[0].index("vote ") + 5):]
            options_raw = [(x[:x.index(" ")].strip(), x[x.index(" "):].strip()) for x in lines[1:]]

            return MessageData(question, options_raw)
        else:
            return None

    async def handle_vote(self, context: Context):
        data = await self.get_message_data(context.message)
        if data is None:
            await context.message.channel.send(messages.Messages.vote_format)
            return

        if len(data.options) == 0:
            return

        for o in data.options:
            try:
                await context.message.add_reaction(o[0])
            except HTTPException:
                await context.message.channel.send(messages.Messages.vote_not_emoji
                                                   .format(not_emoji=o[0]))

        await context.message.channel.send(messages.Messages.vote_none)

        pass

    # The lookups in this method are so ineffective that they make me sick a bit.
    # We could definitely get rid of all the iterations.
    async def handle_reaction(self, target_msg: Message):
        data = await self.get_message_data(target_msg)

        bot_msg = await target_msg.channel.history(limit=3, after=target_msg.created_at)\
            .get(author__id=self.bot.user.id)

        if bot_msg is None:
            return

        r = [x for x in target_msg.reactions if any(str(x.emoji) == a[0] for a in data.options)]

        most_voted = max(r, key=lambda x: x.count)
        all_most_voted = list(filter(lambda x: x.count == most_voted.count, r))

        if most_voted.count == 1:
            await bot_msg.edit(content=messages.Messages.vote_none)
            return

        if len(all_most_voted) == 1:
            option = [a[1] for a in data.options if str(most_voted.emoji) == a[0]][0]

            await bot_msg.edit(content=messages.Messages.vote_winning
                               .format(winning_emoji=most_voted.emoji,
                                       winning_option=option,
                                       votes=most_voted.count))
        else:
            emoji_str = ""
            for e in all_most_voted:
                emoji_str += str(e.emoji) + ", "
            emoji_str = emoji_str[:-2]
            await bot_msg.edit(content=messages.Messages.vote_winning_multiple
                               .format(winning_emojis=emoji_str,
                                       votes=most_voted.count))
