import asyncio
from datetime import datetime

import aiohttp
import disnake

from utils.errors import ApiError


def custom_footer(author: disnake.User, url: str) -> str:
    return f"📩 {author} | {url} • {datetime.now().strftime('%d.%m.%Y %H:%M')}"


async def get_xkcd(rubbergod_session: aiohttp.ClientSession, url: str) -> dict:
    try:
        async with rubbergod_session.get(url) as resp:
            if resp.status != 200:
                raise ApiError(resp.status)
            res = await resp.json()
        return res
    except (aiohttp.ClientConnectorError, asyncio.TimeoutError) as error:
        raise ApiError(str(error))


async def create_xkcd_embed(xkcd_post: dict, user: disnake.User, xkcd_url: str) -> disnake.Embed:
    embed = disnake.Embed(
        title=xkcd_post["title"],
        description=xkcd_post["alt"],
        url=xkcd_url,
    )
    embed.set_image(url=xkcd_post["img"])
    embed.set_footer(text=custom_footer(user, xkcd_url))
    return embed
