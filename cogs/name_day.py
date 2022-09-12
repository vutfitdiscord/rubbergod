import disnake
import aiohttp
import asyncio
from datetime import date, time
from disnake.ext import commands, tasks

from config.app_config import config
from config.messages import Messages


class Nameday(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.send_names.start()

    async def _svatek(self):
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            try:
                url = f"http://svatky.adresa.info/json?date={date.today().strftime('%d%m')}"
                async with session.get(url) as resp:
                    res = await resp.json()
                names = []
                for i in res:
                    names.append(i["name"])
                return Messages.name_day_cz.format(name=", ".join(names))
            except (asyncio.exceptions.TimeoutError, aiohttp.client_exceptions.ClientConnectorError):
                return "Website unreachable"

    async def _meniny(self):
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            try:
                url = f"http://svatky.adresa.info/json?lang=sk&date={date.today().strftime('%d%m')}"
                async with session.get(url) as resp:
                    res = await resp.json()
                names = []
                for i in res:
                    names.append(i["name"])
                return Messages.name_day_sk.format(name=", ".join(names))
            except (asyncio.exceptions.TimeoutError, aiohttp.client_exceptions.ClientConnectorError):
                return "Website unreachable"

    async def _narozeniny(self):
        headers = {"ApiKey": config.grillbot_api_key}
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10), headers=headers) as session:
            try:
                url = "https://grillbot.cloud/api/user/birthday/today"
                async with session.get(url) as resp:
                    birthday = await resp.json()
                    return birthday['message']
            except (asyncio.exceptions.TimeoutError, aiohttp.client_exceptions.ClientConnectorError):
                return "Website unreachable"

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

    @tasks.loop(time=time(22, 00, 1))       # UTC time
    async def send_names(self):
        svatek = await self._svatek()
        meniny = await self._meniny()
        narozeniny = await self._narozeniny()

        bot_room = self.bot.get_channel(config.bot_room)
        await bot_room.send(f"{svatek}\n{meniny}\n{narozeniny}")


def setup(bot):
    bot.add_cog(Nameday(bot))
