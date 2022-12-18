import requests

import disnake
from disnake.ext import commands

from config.app_config import config
from config.messages import Messages
import utils


class Weather(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="pocasi", description=Messages.weather_brief)
    async def weather(self, inter: disnake.ApplicationCommandInteraction, place: str = "Brno"):
        await inter.response.defer()
        token = config.weather_token

        place = place[:100]
        if "&" in place:
            return await inter.edit_original_response("Takhle se žádné město určitě nejmenuje.")

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


def setup(bot):
    bot.add_cog(Weather(bot))
