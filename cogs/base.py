"""
Base cog class. All cogs should inherit from this class.
"""
from functools import cached_property

import disnake

from config.app_config import config


class Base:
    config = config

    def __init__(self):
        self.tasks = []

    @cached_property
    def mod_room(self) -> disnake.TextChannel:
        return self.bot.get_channel(self.config.mod_room)

    @cached_property
    def submod_helper_room(self) -> disnake.TextChannel:
        return self.bot.get_channel(self.config.submod_helper_room)

    @cached_property
    def log_channel(self) -> disnake.TextChannel:
        return self.bot.get_channel(self.config.log_channel)

    @cached_property
    def bot_room(self) -> disnake.TextChannel:
        return self.bot.get_channel(self.config.bot_room)

    @cached_property
    def bot_dev_channel(self) -> disnake.TextChannel:
        return self.bot.get_channel(self.config.bot_dev_channel)

    def cog_unload(self) -> None:
        for task in self.tasks:
            task.cancel()
