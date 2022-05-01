from io import BytesIO
import disnake
from disnake.ext import commands
import json

from config.app_config import config


class GrillbotApi(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        """Api point for grillbot"""
        if message.author.id not in config.grillbot_ids:
            return

        lines = message.content.split('\n')
        if not (lines[0] == '```json' and lines[-1] == '```'):
            return
        lines = lines[1:-1]
        content = '\n'.join(lines)
        request = json.loads(content)
        if "method" not in request or request["method"] not in config.grillbot_api_supported_methods:
            await message.reply("Unsupported method")
            return
        params = request["parameters"]
        cog = self.bot.get_cog(request["method"])
        # check if cog is loaded
        if cog:
            status, content = cog.api(message, params)
            if status != 0:
                await message.reply(content)
                return
            res_json = json.dumps(content)
            with BytesIO(bytes(res_json, 'utf-8')) as file_binary:
                await message.reply(file=disnake.File(fp=file_binary, filename="res.json"))
        else:
            await message.reply("Extension not loaded")



def setup(bot):
    bot.add_cog(GrillbotApi(bot))
