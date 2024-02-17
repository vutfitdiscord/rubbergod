from disnake import Embed, TextChannel
from disnake.ext.commands import Bot


class BaseFeature:
    def __init__(self, bot: Bot):
        self.bot = bot

    async def reply_to_channel(self, channel: TextChannel, message: str = None, embed: Embed = None):
        if message is None and embed is None:
            raise ValueError('Reply required message or embed')

        await channel.send(message, embed=embed)
