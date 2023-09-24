"""
Functions and commands that communicate with the Grillbot API.
"""

import asyncio
import json
from io import BytesIO

import aiohttp
import disnake
from disnake.ext import commands

from cogs.base import Base


class GrillbotApi(Base, commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self._owner_id = bot.owner_id

    async def owner_id(self):
        if not self._owner_id:
            app_info = await self.bot.application_info()
            self._owner_id = app_info.owner.id
        return str(self._owner_id)

    async def post_karma_store(self, karma_objects):
        """send karma objects to grillbot api"""
        if len(karma_objects) == 0:
            return
        headers = {"ApiKey": self.config.grillbot_api_key, "Author": await self.owner_id()}
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10), headers=headers) as session:
            try:
                url = f"{self.config.grillbot_api_url}/user/karma/store"
                data = [{
                        "member_ID": data.member_ID,
                        "karmaValue": data.karma,
                        "positive": data.positive,
                        "negative": data.negative
                        } for data in karma_objects]
                async with session.post(url, json=data):
                    pass
            except (asyncio.exceptions.TimeoutError, aiohttp.client_exceptions.ClientConnectorError):
                pass

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        """Api point for grillbot"""
        if message.author.id not in self.config.grillbot_ids:
            return

        lines = message.content.split('\n')
        if not (lines[0] == '```json' and lines[-1] == '```'):
            return
        lines = lines[1:-1]
        content = '\n'.join(lines)
        request = json.loads(content)
        if "method" not in request or request["method"] not in self.config.grillbot_api_supported_methods:
            await message.reply("Unsupported method")
            return
        params = request["parameters"]
        cog = self.bot.get_cog(request["method"])
        # check if cog is loaded
        if cog:
            status, content = await cog.api(message, params)
            if status != 0:
                await message.reply(content)
                return
            if isinstance(content, disnake.File):
                await message.reply(file=content)
                return
            res_json = json.dumps(content)
            with BytesIO(bytes(res_json, 'utf-8')) as file_binary:
                await message.reply(file=disnake.File(fp=file_binary, filename="res.json"))
        else:
            await message.reply("Extension not loaded")


def setup(bot):
    bot.add_cog(GrillbotApi(bot))
