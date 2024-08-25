import asyncio

import aiohttp
import disnake

import utils
from permissions.custom_errors import ApiError

from .messages_cz import MessagesCZ


async def urban_embeds(author: disnake.User, dict: dict) -> list[disnake.Embed]:
    """Generate embeds from dictionary of responses"""
    embed_list = []

    for idx, item in enumerate(dict["list"]):
        definition = item["definition"]
        example = item["example"]

        if len(definition) > 1024:
            definition = definition[0:1021] + "`…`"
        if len(example) > 1024:
            example = example[0:1021] + "`…`"

        embed = disnake.Embed(
            title=item["word"],
            url=item["permalink"],
        )
        embed.add_field(name="Definition", value=definition, inline=False)
        if example:
            embed.add_field(name="Example", value=example, inline=False)
        embed.add_field(
            name="Page",
            value=f"{idx + 1}/{len(dict['list'])}",
            inline=False,
        )
        utils.embed.add_author_footer(embed, author)

        embed_list.append(embed)

    return embed_list


async def nasa_daily_image(rubbergod_session: aiohttp.ClientSession, nasa_token: str) -> dict:
    url = f"https://api.nasa.gov/planetary/apod?api_key={nasa_token}&concept_tags=True"
    try:
        async with rubbergod_session.get(url) as resp:
            response = await resp.json()
            if "error" in response:
                raise ApiError(response["error"])
            return response
    except (aiohttp.ClientConnectorError, asyncio.exceptions.TimeoutError) as error:
        raise ApiError(str(error))


async def create_nasa_embed(author: disnake.User, response: dict) -> tuple[disnake.Embed, str | None]:
    """
    Create embed for NASA API response
    """
    embed = disnake.Embed(
        title=response["title"],
        description=response["explanation"],
        url=MessagesCZ.nasa_url,
        color=disnake.Color.blurple(),
    )
    url = response["hdurl"] if response.get("hdurl", None) else response["url"]
    utils.embed.add_author_footer(embed, author)
    if response.get("media_type", None) != "video":
        embed.set_image(url=url)
        return embed, None
    return embed, url
