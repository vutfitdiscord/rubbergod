from __future__ import annotations

from disnake import Colour


class RubbergodColors(Colour):
    def __init__(self, value: int) -> None:
        super().__init__(value)

    @classmethod
    def bright_red(cls) -> RubbergodColors:
        """A factory method that returns a :class:`RubbergodColors` with a value of ``0xCB410B``."""
        return cls(0xCB410B)

    @classmethod
    def bright_green(cls) -> RubbergodColors:
        """A factory method that returns a :class:`RubbergodColors` with a value of ``0x34CB0B``."""
        return cls(0x34CB0B)
