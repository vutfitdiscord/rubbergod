import discord
from discord.ext import commands
import re
import os
import toml
from datetime import datetime
import importlib

import utils
import config.app_config as Config_module
from config.messages import Messages

Config = Config_module.Config()

class DynamicConfig(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.check(utils.is_bot_owner)
    @commands.group(pass_context=True)
    async def config(self, ctx):
        """
        Group of commands for dynamicaly changing config
        """
        if ctx.invoked_subcommand is None:
            await ctx.send(Messages.config_help)

    @config.command(name="set")
    async def set_value(self, ctx, key=None, *value):
        """
        Dynamicaly change config values
        """
        if key is None or not value:
            await ctx.send(Messages.config_set_format)
            return
        await self.change_value(ctx, key, list(value), False)

    @config.command()
    async def append(self, ctx, key=None, *value):
        """
        Append value(s) to existing config
        For string and int types command has same bahaviour as `set_value`.
        """
        if key is None or not value:
            await ctx.send(Messages.config_append_format)
            return
        await self.change_value(ctx, key, list(value), True)

    @config.command()
    async def load(self, ctx):
        """
        Load config from `config.toml`
        """
        global Config
        importlib.reload(Config_module)
        Config = Config_module.Config()
        await ctx.send(Messages.config_loaded)

    @config.command(name="list")
    async def list_all(self, ctx):
        keys = dir(Config)
        output = "```"
        for key in keys[:]:
            if not re.match(r"__.*__", key) and key not in Config.config_static:
                output += key + "\n"
        output += "```"
        await ctx.send(output)

    @config.command()
    async def get(self, ctx, key=None):
        """
        Get value of specified key
        """
        if key is None:
            await ctx.send(Messages.config_get_format)
            return
        if not hasattr(Config, key) or key in Config.config_static:
            await ctx.send(Messages.config_wrong_key)
            return
        value = getattr(Config, key)
        embed = discord.Embed(title=key, description=str(value))
        await ctx.send(embed=embed)

    @config.command()
    async def backup(self, ctx):
        """
        Create backup from current config. Backup filename will contain current date.
        """
        config_path = os.path.dirname(__file__)[:-4] + "config/config_backup_"
        config_path += str(datetime.now().date()) + ".toml"
        with open(config_path, "w+") as fd:
            toml.dump(Config.toml_dict, fd)
        await ctx.send(Messages.config_backup_created)

    async def change_value(self, ctx, key:str, value:list, append:bool):
        """
        Changes config atrribute specified by `key` to `value`.
        If `append` values are appended to current setting.
        """
        if not hasattr(Config, key) or key in Config.config_static:
            await ctx.send(Messages.config_wrong_key)
            return
        config_path = os.path.dirname(__file__)[:-4] + "config/config.toml"
        key_toml = key
        key_split = key.split('_', 1)
        for section in Config.toml_dict:
            if key_split[0] == section:
                key_toml = key_split[1]
            if key_toml in Config.toml_dict[section]:
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
                    value = tuple(list(attr) + value)
                elif isinstance(attr, str):
                    value = " ".join(value)
                elif isinstance(attr, int):
                    try:
                        value = int(value[0])
                    except ValueError:
                        await ctx.send(Messages.config_wrong_type)
                        return
                Config.toml_dict[section][key_toml] = value
                break
            else:
                key_toml = key
        else:
            await ctx.send(Messages.config_wrong_key)
            return
        setattr(Config, key, value)
        with open(config_path, "w+") as fd:
            toml.dump(Config.toml_dict, fd)
        await ctx.send(Messages.config_updated)

    @config.error
    async def configerror(self, ctx, error):
        """
        Error in case of insufficient rights for command
        """
        if isinstance(error, commands.CheckFailure):
            await ctx.send(utils.fill_message("insufficient_rights", user=ctx.author.id))


def setup(bot):
    bot.add_cog(DynamicConfig(bot))
