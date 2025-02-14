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


class CustomError(commands.CommandError):
    """An error allowing to set custom message."""

    def __init__(self, error: str) -> None:
        self.message = error


class PermissionError(commands.CommandError):
    """An error indicating that the user doesn't have the required permissions."""

    def __init__(self, message: str) -> None:
        self.message = message


class InvalidRoomError(commands.CommandError):
    """An error indicating that this interaction is only possible in given room."""

    def __init__(self, message: str) -> None:
        self.message = message
