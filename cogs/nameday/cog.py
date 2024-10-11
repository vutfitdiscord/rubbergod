"""
Cog for sending name days and birthdays.
"""

from datetime import date, time

import disnake
from disnake.ext import commands, tasks

import utils
from cogs.base import Base
from rubbergod import Rubbergod
from utils.checks import PermissionsCheck
from utils.errors import ApiError

from .messages_cz import MessagesCZ


class Nameday(Base, commands.Cog):
    def __init__(self, bot: Rubbergod):
        super().__init__()
        self.bot = bot
        self.tasks = [self.send_names.start()]

    async def _name_day_cz(self, task: bool = False) -> str:
        url = f"http://svatky.adresa.info/json?date={date.today().strftime('%d%m')}"
        try:
            async with self.bot.rubbergod_session.get(url) as resp:
                names: dict = await resp.json()
            return MessagesCZ.name_day_cz(name=", ".join(i["name"] for i in names))
        except Exception as error:
            if task:
                # tasks can't handle exceptions and will stop working
                return MessagesCZ.api_error(error=error)
            raise ApiError(str(error))

    async def _name_day_sk(self, task: bool = False) -> str:
        url = f"http://svatky.adresa.info/json?lang=sk&date={date.today().strftime('%d%m')}"
        try:
            async with self.bot.rubbergod_session.get(url) as resp:
                names_list = await resp.json()
            return MessagesCZ.name_day_sk(name=", ".join(i["name"] for i in names_list))
        except Exception as error:
            if task:
                # tasks can't handle exceptions and will stop working
                return MessagesCZ.api_error(error=error)
            raise ApiError(str(error))

    async def _birthday(self) -> str:
        url = f"{self.config.grillbot_api_url}/user/birthday/today"
        try:
            async with self.bot.grillbot_session.get(url) as resp:
                birthday = await resp.json()
                return birthday["message"]
        except Exception as error:
            return MessagesCZ.api_error(error=error)

    @commands.slash_command(name="svatek", description=MessagesCZ.name_day_cz_brief)
    async def name_day_cz(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=PermissionsCheck.is_botroom(inter))
        name_day_cz = await self._name_day_cz()
        await inter.edit_original_response(name_day_cz)

    @commands.slash_command(name="meniny", description=MessagesCZ.name_day_sk_brief)
    async def name_day_sk(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=PermissionsCheck.is_botroom(inter))
        name_day_sk = await self._name_day_sk()
        await inter.edit_original_response(name_day_sk)

    @tasks.loop(time=time(7, 0, tzinfo=utils.general.get_local_zone()))
    async def send_names(self):
        name_day_cz = await self._name_day_cz(task=True)
        name_day_sk = await self._name_day_sk(task=True)
        birthday = await self._birthday()
        mentions = disnake.AllowedMentions.none()
        await self.bot_room.send(f"{name_day_cz}\n{name_day_sk}\n{birthday}", allowed_mentions=mentions)
