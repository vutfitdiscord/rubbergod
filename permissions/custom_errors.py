"""Custom error classes."""
from disnake.ext import commands

from config.messages import Messages


class InvalidTime(commands.CommandError):
    """An error indicating that the time format is invalid.
    """
    def __init__(self, time_format: str) -> None:
        self.message = Messages.invalid_time_format(time_format=time_format)
