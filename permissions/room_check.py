"""
Verify room permissions and determine if ephemeral messaging is necessary.
"""

import disnake
from disnake.ext import commands

from config.app_config import config
from rubbergod import Rubbergod


def is_in_modroom(ctx: commands.Context | disnake.ApplicationCommandInteraction):
    """Check if the command is invoked in modroom"""
    return ctx.channel.id == config.mod_room


def is_in_voteroom(ctx: commands.Context | disnake.ApplicationCommandInteraction):
    """Check if the command is invoked in voteroom"""
    return ctx.channel.id == config.vote_room


class RoomCheck:
    def __init__(self, bot: Rubbergod):
        self.bot = bot

    def botroom_check(self, inter) -> bool:
        """
        returns False/True if we want ephemeral command
        False if:
            1. in DMs with bot
            2. in thread
            3. in allowed channel
        else True
        """

        # DMs with bot
        if inter.guild is None:
            return False

        # allow threads in channels
        if isinstance(inter.channel, disnake.Thread):
            return False

        # allowed channels
        if inter.channel_id in config.allowed_channels:
            return False

        return True
