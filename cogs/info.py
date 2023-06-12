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
from config.app_config import config
from config.messages import Messages


class Info(Base, commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    def urban_embeds(self, author, dict):
        """Generate embeds from dictionary of resposes"""
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
            utils.add_author_footer(embed, author)

            embed_list.append(embed)

        return embed_list

    async def urban_pages(self, inter, embeds):
        """Send message and handle pagination for 300 seconds"""
        view = EmbedView(inter.author, embeds)
        view.message = await inter.edit_original_response(embed=embeds[0], view=view)

    @cooldowns.short_cooldown
    @commands.slash_command(name="urban", description=Messages.urban_brief)
    async def urban(self, inter: disnake.ApplicationCommandInteraction, expression):
        """Finding expression and shorcuts in urban directory"""

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
            await inter.edit_original_response(Messages.urban_not_found)
        return

    @commands.slash_command(name="pocasi", description=Messages.weather_brief)
    async def weather(self, inter: disnake.ApplicationCommandInteraction, place: str = "Brno"):
        await inter.response.defer()
        token = config.weather_token

        place = place[:100]
        if "&" in place:
            await inter.edit_original_response("Takhle se žádné město určitě nejmenuje.")
            return

        url = (
            "http://api.openweathermap.org/data/2.5/weather?q="
            + place
            + "&units=metric&lang=cz&appid="
            + token
        )
        res = requests.get(url, timeout=10).json()

        if str(res["cod"]) == "200":
            description = "Aktuální počasí v městě " + res["name"] + ", " + res["sys"]["country"]
            embed = disnake.Embed(title="Počasí", description=description)
            image = "http://openweathermap.org/img/w/" + res["weather"][0]["icon"] + ".png"
            embed.set_thumbnail(url=image)
            weather = res["weather"][0]["main"] + " ( " + res["weather"][0]["description"] + " ) "
            temp = str(res["main"]["temp"]) + "°C"
            feels_temp = str(res["main"]["feels_like"]) + "°C"
            humidity = str(res["main"]["humidity"]) + "%"
            wind = str(res["wind"]["speed"]) + "m/s"
            clouds = str(res["clouds"]["all"]) + "%"
            visibility = str(res["visibility"] / 1000) + " km" if "visibility" in res else "bez dat"
            embed.add_field(name="Počasí", value=weather, inline=False)
            embed.add_field(name="Teplota", value=temp, inline=True)
            embed.add_field(name="Pocitová teplota", value=feels_temp, inline=True)
            embed.add_field(name="Vlhkost", value=humidity, inline=True)
            embed.add_field(name="Vítr", value=wind, inline=True)
            embed.add_field(name="Oblačnost", value=clouds, inline=True)
            embed.add_field(name="Viditelnost", value=visibility, inline=True)

            utils.add_author_footer(embed, inter.author)

            await inter.edit_original_response(embed=embed)

        elif str(res["cod"]) == "404":
            await inter.edit_original_response("Město nenalezeno")
        elif str(res["cod"]) == "401":
            await inter.edit_original_response("Rip token -> Rebel pls fix")
        else:
            await inter.edit_original_response(
                "Město nenalezeno! <:pepeGun:484470874246742018> (" + res["message"] + ")"
            )

    @commands.slash_command(name="kreditovy_strop", description=Messages.credit_limit_brief)
    async def kreditovy_strop(self, inter):
        """
        Prints annual credit limit criteria
        """
        await inter.send(Messages.credit_limit_info)


def setup(bot):
    bot.add_cog(Info(bot))
