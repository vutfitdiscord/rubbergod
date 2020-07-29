import discord
from discord.ext import commands
import re
import os
import toml
from datetime import datetime

import utils
from config.app_config import Config
from config.messages import Messages


class DynamicConfig(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.check(utils.is_bot_owner)
    @commands.group(pass_context=True)
    async def config(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(Messages.config_help)

    @config.command(name="set")
    async def set_value(self, ctx, key=None, *value):
        if key is None:
            await ctx.send(Messages.config_set_format)
            return
        await self.change_value(ctx, key, list(value), False)

    @config.command()
    async def update(self, ctx, key=None, *value):
        if key is None:
            await ctx.send(Messages.config_update_format)
            return
        await self.change_value(ctx, key, list(value), True)

    @config.command(name="list")
    async def list_all(self, ctx):
        keys = dir(Config)
        output = "```"
        for key in keys[:]:
            if not re.match(r"__.*__", key):
                output += key + "\n"
        output += "```"
        await ctx.send(output)

    @config.command()
    async def get(self, ctx, key=None):
        if key is None:
            await ctx.send(Messages.config_get_format)
            return
        if not hasattr(Config, key):
            await ctx.send(Messages.config_wrong_key)
            return
        value = getattr(Config, key)
        embed = discord.Embed(title=key, description=str(value))
        await ctx.send(embed=embed)

    @config.command()
    async def backup(self, ctx):
        config_path = os.path.dirname(__file__)[:-4] + "config/config_backup_"
        config_path += str(datetime.now().date()) + ".toml"
        with open(config_path, "w+") as fd:
            toml.dump(Config.toml_dict, fd)
        await ctx.send(Messages.config_backup_created)

    async def change_value(self, ctx, key, value, append):
        if not hasattr(Config, key):
            ctx.send(Messages.config_wrong_key)
            return
        config_path = os.path.dirname(__file__)[:-4] + "config/config.toml"
        for section in Config.toml_dict:
            if key in Config.toml_dict[section]:
                attr = getattr(Config, key)
                if isinstance(attr, list):
                    if isinstance(attr[0], int):
                        for idx, item in enumerate(value):
                            try:
                                value[idx] = int(item)
                            except ValueError:
                                await ctx.send(Messages.config_wrong_type)
                                return
                    if append:
                        value = attr + value
                elif isinstance(attr, tuple) and append:
                    value = tuple(list(attr) + key)
                elif isinstance(attr, int):
                    try:
                        value = int(value[0])
                    except ValueError:
                        await ctx.send(Messages.config_wrong_type)
                        return
                Config.toml_dict[section][key] = value
                break
        else:
            await ctx.send(Messages.config_wrong_key)
            return
        setattr(Config, key, value)
        with open(config_path, "w+") as fd:
            toml.dump(Config.toml_dict, fd)
        await ctx.send(Messages.config_updated)


def setup(bot):
    bot.add_cog(DynamicConfig(bot))
