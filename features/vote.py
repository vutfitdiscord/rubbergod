from discord import Message, HTTPException
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

    async def get_message_data(self, context: Context):
        message = context.message.content

        if len(message.split()) < 2:
            return None

        if message[1:].startswith("vote") and message[0] in config.Config.command_prefix:
            lines = message.splitlines()
            question = lines[0][(lines[0].index("vote ") + 5):]
            options_raw = [(x[:x.index(" ")].strip(), x[x.index(" "):].strip()) for x in lines[1:]]

            return MessageData(question, options_raw)
        else:
            return None

    async def handle_vote(self, context: Context):
        data = await self.get_message_data(context)
        if data is None:
            await context.message.channel.send(messages.Messages.vote_format)
            return

        for o in data.options:
            try:
                await context.message.add_reaction(o[0])
            except HTTPException:
                await context.message.channel.send(messages.Messages.vote_not_emoji
                                                   .format(not_emoji=o[0]))

        pass

    async def handle_reaction(self, target_msg: Message):

        pass