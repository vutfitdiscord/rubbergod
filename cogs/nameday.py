"""
Cog for sending name days and birthdays.
"""

import asyncio
from datetime import date, time

import aiohttp
import disnake
from disnake.ext import commands, tasks

import utils
from cogs.base import Base
from config.messages import Messages
from permissions import room_check


class Nameday(Base, commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self._owner_id = bot.owner_id
        self.check = room_check.RoomCheck(bot)
        self.tasks = [self.send_names.start()]

    async def owner_id(self):
        if not self._owner_id:
            app_info = await self.bot.application_info()
            self._owner_id = app_info.owner.id
        return str(self._owner_id)

    async def _name_day_cz(self):
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            try:
                url = f"http://svatky.adresa.info/json?date={date.today().strftime('%d%m')}"
                async with session.get(url) as resp:
                    res = await resp.json()
                names = []
                for i in res:
                    names.append(i["name"])
                return Messages.name_day_cz(name=", ".join(names))
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
                return Messages.name_day_sk(name=", ".join(names))
            except (asyncio.exceptions.TimeoutError, aiohttp.client_exceptions.ClientConnectorError):
                return "Website unreachable"

    async def _birthday(self):
        headers = {"ApiKey": self.config.grillbot_api_key, "Author": await self.owner_id()}
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10), headers=headers) as session:
            try:
                url = f"{self.config.grillbot_api_url}/user/birthday/today"
                async with session.get(url) as resp:
                    birthday = await resp.json()
                    return birthday['message']
            except (asyncio.exceptions.TimeoutError, aiohttp.client_exceptions.ClientConnectorError):
                return Messages.birthday_api_error

    @commands.slash_command(name="svatek", description=Messages.name_day_cz_brief)
    async def name_day_cz(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=self.check.botroom_check(inter))
        name_day_cz = await self._name_day_cz()
        await inter.edit_original_response(name_day_cz)

    @commands.slash_command(name="meniny", description=Messages.name_day_sk_brief)
    async def name_day_sk(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=self.check.botroom_check(inter))
        name_day_sk = await self._name_day_sk()
        await inter.edit_original_response(name_day_sk)

    @tasks.loop(time=time(7, 0, tzinfo=utils.get_local_zone()))
    async def send_names(self):
        name_day_cz = await self._name_day_cz()
        name_day_sk = await self._name_day_sk()
        birthday = await self._birthday()

        await self.bot_room.send(f"{name_day_cz}\n{name_day_sk}\n{birthday}")


def setup(bot):
    bot.add_cog(Nameday(bot))
