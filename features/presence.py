import datetime

import discord
from discord.ext.commands import Bot

from config.app_config import config
from features.base_feature import BaseFeature
from features.git import Git


class Presence(BaseFeature):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.git = Git()

        self.activity = discord.Game(
            start=datetime.datetime.utcnow(),
            name=config.default_prefix + 'god'
            f' | Running hash {self.git.short_hash()}')

    async def set_presence(self):
        await self.bot.change_presence(activity=self.activity)
