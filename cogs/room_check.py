import utils
from config import messages, config

config = config.Config
messages = messages.Messages


class RoomCheck():

    def __init__(self, bot):
        self.bot = bot

    async def botroom_check(self, message):
        room = await self.get_room(message)
        if room is not None and room.id not in config.allowed_channels:
            await message.channel.send(messages.bot_room_redirect.format(
                utils.generate_mention(message.author.id),
                config.bot_room))

    async def get_room(self, message):
        guild = self.bot.get_guild(config.guild_id)
        try:
            if message.channel.guild == guild:
                return message.channel
        except AttributeError:
            # Jsme v PM
            return None

    async def guild_check(self, message):
        try:
            guild = self.bot.get_guild(config.guild_id)
            return message.channel.guild == guild
        except AttributeError:
            return False
