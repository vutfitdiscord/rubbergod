"""
Cog containing commands that get basic information from other sources.
examples - urban meaning of word, weather at location
"""

import disnake
import requests
from disnake.ext import commands

import utils
from buttons.embed import EmbedView
from cogs.base import Base
from config import cooldowns
from rubbergod import Rubbergod

from .messages_cz import MessagesCZ


class Info(Base, commands.Cog):
    def __init__(self, bot: Rubbergod):
        super().__init__()
        self.bot = bot

    def urban_embeds(self, author: disnake.User, dict: dict) -> list[disnake.Embed]:
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

    async def urban_pages(
        self, inter: disnake.ApplicationCommandInteraction, embeds: list[disnake.Embed]
    ) -> None:
        """Send message and handle pagination for 300 seconds"""
        view = EmbedView(inter.author, embeds)
        view.message = await inter.edit_original_response(embed=embeds[0], view=view)

    @cooldowns.short_cooldown
    @commands.slash_command(name="urban", description=MessagesCZ.urban_brief)
    async def urban(self, inter: disnake.ApplicationCommandInteraction, expression) -> None:
        """Finding expression and shortcuts in urban directory"""

        await inter.response.defer(with_message=True)
        embeds = None
        try:
            response = requests.get(f"http://api.urbandictionary.com/v0/define?term={expression}", timeout=10)
            dict = response.json()
            response.raise_for_status()

        except requests.HTTPError as http_err:
            await inter.edit_original_response(f"HTTP error occurred: {http_err}")
        except Exception as err:
            await inter.edit_original_response(f"Error occurred: {err}")
        else:
            # Request was successful
            embeds = self.urban_embeds(inter.author, dict)

        if embeds:
            await self.urban_pages(inter, embeds)
        else:
            await inter.edit_original_response(MessagesCZ.urban_not_found)

    @commands.slash_command(name="pocasi", description=MessagesCZ.weather_brief)
    async def weather(self, inter: disnake.ApplicationCommandInteraction, place: str = "Brno") -> None:
        await inter.response.defer()
        token = self.config.weather_token

        place = place[:100]
        if "&" in place:
            await inter.edit_original_response(MessagesCZ.invalid_name)
            return

        url = f"http://api.openweathermap.org/data/2.5/weather?q={place}&units=metric&lang=cz&appid={token}"

        res = requests.get(url, timeout=10).json()

        if str(res["cod"]) == "200":
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

        elif str(res["cod"]) == "404":
            await inter.edit_original_response(MessagesCZ.city_not_found)
        elif str(res["cod"]) == "401":
            await inter.edit_original_response(MessagesCZ.token_error)
        else:
            await inter.edit_original_response(MessagesCZ.no_city(result=res["message"]))

    @commands.slash_command(name="kreditovy_strop", description=MessagesCZ.credit_limit_brief)
    async def kreditovy_strop(self, inter: disnake.ApplicationCommandInteraction) -> None:
        """
        Prints annual credit limit criteria
        """
        await inter.send(MessagesCZ.credit_limit_info)
