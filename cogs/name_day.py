import disnake
import requests
from datetime import date

from disnake.ext import commands

from config.messages import Messages


class Name_day(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="svatek", description=Messages.name_day_cz_brief)
    async def svatek(self, inter: disnake.ApplicationCommandInteraction):
        url = f"http://svatky.adresa.info/json?date={date.today().strftime('%d%m')}"
        res = requests.get(url).json()
        names = []
        for i in res:
            names.append(i["name"])
        await inter.response.send_message(Messages.name_day_cz.format(name=", ".join(names)))

    @commands.slash_command(name="meniny", description=Messages.name_day_sk_brief)
    async def meniny(self, inter: disnake.ApplicationCommandInteraction):
        url = f"http://svatky.adresa.info/json?lang=sk&date={date.today().strftime('%d%m')}"
        res = requests.get(url).json()
        names = []
        for i in res:
            names.append(i["name"])
        await inter.response.send_message(Messages.name_day_sk.format(name=", ".join(names)))


def setup(bot):
    bot.add_cog(Name_day(bot))
