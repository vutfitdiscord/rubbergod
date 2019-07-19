from repository.base_repository import BaseRepository
import discord
import datetime


class Presence(BaseRepository):

    def __init__(self, client, utils):
        super().__init__()

        self.client = client
        self.activity = discord.Game(
            start=datetime.datetime.utcnow(),
            name=self.config.command_prefix + 'god'
            ' | Running hash ' + utils.git_hash()[:7])

    async def set_presence(self):
        await self.client.change_presence(activity=self.activity)
