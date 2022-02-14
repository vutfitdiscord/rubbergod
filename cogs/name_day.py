import requests
from datetime import date

from disnake.ext import commands

from config.messages import Messages as messages


class Name_day(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief=messages.name_day_cz_brief)
    async def svatek(self, ctx):
        url = f"http://svatky.adresa.info/json?date={date.today().strftime('%d%m')}"
        res = requests.get(url).json()
        names = []
        for i in res:
            names.append(i["name"])
        await ctx.send(messages.name_day_cz.format(name=", ".join(names)))

    @commands.command(brief=messages.name_day_sk_brief)
    async def meniny(self, ctx):
        url = f"http://svatky.adresa.info/json?lang=sk&date={date.today().strftime('%d%m')}"
        res = requests.get(url).json()
        names = []
        for i in res:
            names.append(i["name"])
        await ctx.send(messages.name_day_sk.format(name=", ".join(names)))


def setup(bot):
    bot.add_cog(Name_day(bot))
