"""
Cog containing commands that get basic information from other sources.
examples - urban meaning of word, weather at location
"""

from __future__ import annotations

import asyncio
from datetime import time

import aiohttp
import disnake
from disnake.ext import commands, tasks

import utils
from buttons.embed import PaginationView
from cogs.base import Base
from permissions.room_check import RoomCheck
from rubbergod import Rubbergod
from utils import cooldowns
from utils.errors import ApiError

from .features import create_nasa_embed, nasa_daily_image, urban_embeds
from .messages_cz import MessagesCZ


class Info(Base, commands.Cog):
    def __init__(self, bot: Rubbergod):
        super().__init__()
        self.bot = bot
        self.check = RoomCheck(bot)
        self.tasks = [self.send_nasa_image.start()]

    @cooldowns.short_cooldown
    @commands.slash_command(name="urban", description=MessagesCZ.urban_brief)
    async def urban(self, inter: disnake.ApplicationCommandInteraction, expression: str) -> None:
        """Finding expression and shortcuts in urban directory"""
        await inter.response.defer()
        url = f"http://api.urbandictionary.com/v0/define?term={expression}"
        try:
            async with self.bot.rubbergod_session.get(url) as response:
                dict = await response.json()
                if response.status != 200:
                    raise ApiError(dict)
        except (aiohttp.ClientConnectorError, asyncio.TimeoutError) as error:
            raise ApiError(str(error))

        embeds = await urban_embeds(inter.author, dict)
        if not embeds:
            await inter.edit_original_response(MessagesCZ.urban_not_found)
            return

        view = PaginationView(inter.author, embeds)
        view.message = await inter.edit_original_response(embed=embeds[0], view=view)

    @commands.slash_command(name="pocasi", description=MessagesCZ.weather_brief)
    async def weather(self, inter: disnake.ApplicationCommandInteraction, place: str = "Brno") -> None:
        await inter.response.defer()
        token = self.config.weather_token

        if "&" in place:
            await inter.edit_original_response(MessagesCZ.invalid_name)
            return

        url = f"http://api.openweathermap.org/data/2.5/weather?q={place}&units=metric&lang=cz&appid={token}"
        try:
            async with self.bot.rubbergod_session.get(url) as response:
                if response.status == 200:
                    res = await response.json()
                elif response.status == 401:
                    await inter.edit_original_response(MessagesCZ.token_error)
                    return
                elif response.status == 404:
                    await inter.edit_original_response(MessagesCZ.city_not_found)
                    return
                else:
                    response = await response.json()
                    await inter.edit_original_response(MessagesCZ.no_city(result=response["message"]))
                    return
        except (aiohttp.ClientConnectorError, asyncio.TimeoutError) as error:
            raise ApiError(str(error))

        description = MessagesCZ.weather_description(city=res["name"], country=res["sys"]["country"])
        embed = disnake.Embed(title="Počasí", description=description)
        image = f"http://openweathermap.org/img/w/{res['weather'][0]['icon']}.png"
        embed.set_thumbnail(url=image)
        weather = f"{res['weather'][0]['main']} ({res['weather'][0]['description']})"
        temp = f"{res['main']['temp']}°C"
        feels_temp = f"{res['main']['feels_like']}°C"
        humidity = f"{res['main']['humidity']}%"
        wind = f"{res['wind']['speed']}m/s"
        clouds = f"{res['clouds']['all']}%"
        visibility = f"{res['visibility'] / 1000} km" if "visibility" in res else "bez dat"
        embed.add_field(name=MessagesCZ.weather, value=weather, inline=False)
        embed.add_field(name=MessagesCZ.temperature, value=temp, inline=True)
        embed.add_field(name=MessagesCZ.feels_like, value=feels_temp, inline=True)
        embed.add_field(name=MessagesCZ.humidity, value=humidity, inline=True)
        embed.add_field(name=MessagesCZ.wind, value=wind, inline=True)
        embed.add_field(name=MessagesCZ.clouds, value=clouds, inline=True)
        embed.add_field(name=MessagesCZ.visibility, value=visibility, inline=True)

        utils.embed.add_author_footer(embed, inter.author)

        await inter.edit_original_response(embed=embed)

    @cooldowns.default_cooldown
    @commands.slash_command(name="nasa_daily_image", description=MessagesCZ.nasa_image_brief)
    async def nasa_image(self, inter: disnake.ApplicationCommandInteraction) -> None:
        ephemeral = self.check.botroom_check(inter)
        await inter.response.defer(ephemeral=ephemeral)
        response = await nasa_daily_image(self.bot.rubbergod_session, self.config.nasa_token)
        embed, video = await create_nasa_embed(inter.author, response)
        await inter.edit_original_response(embed=embed)
        if video:
            await inter.send(video, ephemeral=ephemeral)

    @tasks.loop(time=time(7, 0, tzinfo=utils.general.get_local_zone()))
    async def send_nasa_image(self):
        response = await nasa_daily_image(self.bot.rubbergod_session, self.config.nasa_token)
        embed, video = await create_nasa_embed(self.bot.user, response)
        await self.space_channel.send(embed=embed)
        if video:
            await self.space_channel.send(video)

    @commands.slash_command(name="kreditovy_strop", description=MessagesCZ.credit_limit_brief)
    async def kreditovy_strop(self, inter: disnake.ApplicationCommandInteraction) -> None:
        """
        Prints annual credit limit criteria
        """
        await inter.send(MessagesCZ.credit_limit_info)
