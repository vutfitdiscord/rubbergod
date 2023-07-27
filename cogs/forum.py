"""
Cog managing threads in forums (auto-archive, etc.).
"""

import disnake
from disnake.ext import commands

from cogs.base import Base


class Forum(Base, commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_thread_update(self, thread: disnake.Thread):
        """archive thread in 24 hours of inactivity after it is tagged for archivation"""
        if thread.parent_id not in self.config.forum_autoclose_forums:
            return

        # can't edit archived threads
        if thread.archived:
            return

        after_tags = [tag.name.lower() for tag in thread.applied_tags]
        one_day = 1440

        # removed archivation tag from still active thread - reset archive timer
        if (
            thread.auto_archive_duration != one_day*7
            and not any(tag in after_tags for tag in self.config.forum_tags)
        ):
            await thread.edit(auto_archive_duration=one_day*7)
            return
        # thread tagged for archivation
        if any(tag in after_tags for tag in self.config.forum_tags):
            await thread.edit(auto_archive_duration=one_day)
            return


def setup(bot):
    bot.add_cog(Forum(bot))
