"""Custom error classes."""

from disnake.ext import commands

from config.messages import Messages


class InvalidTime(commands.CommandError):
    """An error indicating that the time format is invalid."""

    def __init__(self, time_format: str) -> None:
        self.message = Messages.invalid_time_format(time_format=time_format)


class ApiError(commands.CommandError):
    """An error indicating that the api returned invalid status."""

    def __init__(self, error: str) -> None:
        self.message = Messages.api_error(error=error)


class NotHelperPlusError(commands.CommandError):
    """An error indicating that a user doesn't have permissions to use
    a command that is available only to helpers and above.
    """

    def __init__(self) -> None:
        self.message = Messages.helper_plus_only


class NotSubmodPlusError(commands.CommandError):
    """An error indicating that a user doesn't have permissions to use
    a command that is available only to submods and above.
    """

    def __init__(self) -> None:
        self.message = Messages.submod_plus_only


class NotModPlusError(commands.CommandError):
    """An error indicating that a user doesn't have permissions to use
    a command that is available only to mods and above.
    """

    def __init__(self) -> None:
        self.message = Messages.mod_plus_only


class NotBotAdminError(commands.CommandError):
    """An error indicating that a user doesn't have permissions to use
    a command that is available only to admins of bot.
    """

    def __init__(self) -> None:
        self.message = Messages.bot_admin_only


class InvalidRoomError(commands.CommandError):
    """An error indicating that this interaction is only possible in given room."""

    def __init__(self, message: str) -> None:
        self.message = message
