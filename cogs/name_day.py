import disnake
import requests
from datetime import date, time
from disnake.ext import commands, tasks

from config.app_config import config
from config.messages import Messages


class Nameday(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.send_names.start()

    async def _svatek(self):
        url = f"http://svatky.adresa.info/json?date={date.today().strftime('%d%m')}"
        res = requests.get(url, timeout=10).json()
        names = []
        for i in res:
            names.append(i["name"])
        return Messages.name_day_cz.format(name=", ".join(names))

    async def _meniny(self):
        url = f"http://svatky.adresa.info/json?lang=sk&date={date.today().strftime('%d%m')}"
        res = requests.get(url, timeout=10).json()
        names = []
        for i in res:
            names.append(i["name"])
        return Messages.name_day_sk.format(name=", ".join(names))

    @commands.slash_command(name="svatek", description=Messages.name_day_cz_brief)
    async def svatek(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        svatek = await self._svatek()
        await inter.edit_original_message(svatek)

    @commands.slash_command(name="meniny", description=Messages.name_day_sk_brief)
    async def meniny(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        meniny = await self._meniny()
        await inter.edit_original_message(meniny)

    @tasks.loop(time=time(22, 0, 1))       # UTC time
    async def send_names(self):
        svatek = await self._svatek()
        meniny = await self._meniny()
        bot_room = self.bot.get_channel(config.bot_room)
        await bot_room.send(f"{svatek}\n{meniny}")


def setup(bot):
    bot.add_cog(Nameday(bot))
