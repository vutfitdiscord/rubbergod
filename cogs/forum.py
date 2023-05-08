"""
Cog managing threads in forums (auto-archive, etc.).
"""

import disnake
from disnake.ext import commands

from cogs.base import Base
from config.app_config import config


class Forum(Base, commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_thread_update(self, before: disnake.Thread, after: disnake.Thread):
        """archive thread in 24 hours of inactivity after it is tagged for archivation"""
        if before.parent_id != config.advertising_room:
            return

        # can't edit archived threads
        if before.archived:
            return

        before_tags = [tag.name.lower() for tag in before.applied_tags]
        after_tags = [tag.name.lower() for tag in after.applied_tags]
        one_day = 1440

        # removed archivation tag from still active thread - reset archive timer
        if (
            any(tag in before_tags for tag in config.tags)
            and not any(tag in after_tags for tag in config.tags)
        ):
            return await after.edit(auto_archive_duration=one_day*7)
        # thread tagged for archivation
        if any(tag in after_tags for tag in config.tags):
            return await after.edit(auto_archive_duration=one_day)


def setup(bot):
    bot.add_cog(Forum(bot))
