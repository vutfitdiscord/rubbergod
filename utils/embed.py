from datetime import datetime, timezone
from typing import Iterable

import disnake


def pagination_next(id: str, page: int, max_page: int, roll_around: bool = True) -> int:
    if "next" in id:
        next_page = page + 1
    elif "prev" in id:
        next_page = page - 1
    elif "start" in id:
        next_page = 1
    elif "end" in id:
        next_page = max_page
    if 1 <= next_page <= max_page:
        return next_page
    elif roll_around and next_page == 0:
        return max_page
    elif roll_around and next_page > max_page:
        return 1
    else:
        return 0


def add_author_footer(
    embed: disnake.Embed,
    author: disnake.User | None,
    set_timestamp=True,
    additional_text: Iterable[str] = [],
    anonymous: bool = False,
) -> None:
    """
    Adds footer to the embed with author name and icon from ctx.

    :param author: author info
    :param embed: disnake.Embed object
    :param set_timestamp: bool, should the embed's timestamp be set
    :param additional_text: Iterable of strings that will be joined with author name by pipe symbol, eg.:
    :param anonymous: bool, show author as Anonymous
    "john#2121 | text1 | text2" or "Anonymous | text1 | text2"
    """

    if set_timestamp:
        embed.timestamp = datetime.now(tz=timezone.utc)

    if author is None:
        # sometimes discord returns None even though it shouldn't
        embed.set_footer(icon_url=None, text=" | ".join("Unknown", *additional_text))
        return

    if anonymous:
        display_name = "Anonymous"
        display_avatar = author.default_avatar.url
    else:
        display_name = author.display_name
        display_avatar = author.display_avatar.url

    embed.set_footer(icon_url=display_avatar, text=" | ".join((str(display_name), *additional_text)))
