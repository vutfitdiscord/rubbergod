import asyncio
import io

import aiohttp
import disnake

import utils
from utils.errors import ApiError

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


async def create_nasa_embed(
    rubbergod_session: aiohttp.ClientSession, author: disnake.User, response: dict
) -> tuple[disnake.Embed, str | None]:
    """
    Create embed for NASA API response

    Returns tuple of embed and video url (if media type is video)
    """
    embed = disnake.Embed(
        title=response["title"],
        description=response["explanation"],
        url=MessagesCZ.nasa_url,
        color=disnake.Color.blurple(),
    )
    utils.embed.add_author_footer(embed, author)

    url = response.get("url", None)
    if response.get("media_type", None) == "video":
        return embed, url

    try:
        async with rubbergod_session.get(url) as resp:
            # download image
            if resp.status != 200:
                raise ApiError(MessagesCZ.nasa_image_error)

            image_data = await resp.read()
            nasa_image_file = disnake.File(io.BytesIO(image_data), filename="nasaImage.png")
    except (aiohttp.ClientConnectorError, asyncio.exceptions.TimeoutError) as error:
        raise ApiError(str(error))

    embed.set_image(file=nasa_image_file)
    return embed, None
