class ButtonInteractionError(Exception):
    """An error indicating that the time format is invalid."""

    def __init__(self, author: str, message: str, ephemeral: bool = False) -> None:
        self.message = f"{author} {message}"
        self.ephemeral = ephemeral
