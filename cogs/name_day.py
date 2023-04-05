import asyncio
from datetime import date, time
from functools import cached_property

import aiohttp
import disnake
from disnake.ext import commands, tasks

import utils
from config.app_config import config
from config.messages import Messages


class Nameday(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.send_names.start()

    @cached_property
    async def bot_owner(self):
        bot_owner = await self.bot.application_info()
        return str(bot_owner.owner.id)

    async def _name_day_cz(self):
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

    async def _name_day_sk(self):
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

    async def _birthday(self):
        headers = {"ApiKey": config.grillbot_api_key, "Author": await self.bot_owner}
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10), headers=headers) as session:
            try:
                url = "https://grillbot.cloud/api/user/birthday/today"
                async with session.get(url) as resp:
                    birthday = await resp.json()
                    return birthday['message']
            except (asyncio.exceptions.TimeoutError, aiohttp.client_exceptions.ClientConnectorError):
                return Messages.birthday_api_error

    @commands.slash_command(name="svatek", description=Messages.name_day_cz_brief)
    async def name_day_cz(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        name_day_cz = await self._name_day_cz()
        await inter.edit_original_response(name_day_cz)

    @commands.slash_command(name="meniny", description=Messages.name_day_sk_brief)
    async def name_day_sk(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        name_day_sk = await self._name_day_sk()
        await inter.edit_original_response(name_day_sk)

    @tasks.loop(time=time(7, 0, tzinfo=utils.get_local_zone()))
    async def send_names(self):
        name_day_cz = await self._name_day_cz()
        name_day_sk = await self._name_day_sk()
        birthday = await self._birthday()

        bot_room = self.bot.get_channel(config.bot_room)
        await bot_room.send(f"{name_day_cz}\n{name_day_sk}\n{birthday}")


def setup(bot):
    bot.add_cog(Nameday(bot))
