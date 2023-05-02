"""
Cog for dynamicaly changing config.
"""

import os
import re
from datetime import datetime

import disnake
import toml
from disnake.ext import commands

import utils
from cogs.base import Base
from config.app_config import config, load_config
from config.messages import Messages
from permissions import permission_check


class DynamicConfig(Base, commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.check(permission_check.is_bot_admin)
    @commands.group(pass_context=True)
    async def config(self, ctx):
        """
        Group of commands for dynamicaly changing config
        """
        if ctx.invoked_subcommand is None:
            await ctx.send(utils.get_command_group_signature(ctx))

    @config.command(name="set", brief=Messages.config_set_brief)
    async def set_value(self, ctx, key=None, *value):
        """
        Dynamicaly change config values
        """
        if key is None or not value:
            await ctx.send(utils.get_command_signature(ctx))
            return
        load_config()
        await self.change_value(ctx, key, list(value), False)

    @config.command(brief=Messages.config_append_brief)
    async def append(self, ctx, key=None, *value):
        """
        Append value(s) to existing config
        For string and int types command has same bahaviour as `set_value`.
        """
        if key is None or not value:
            await ctx.send(Messages.config_append_format)
            return
        load_config()
        await self.change_value(ctx, key, list(value), True)

    @config.command(brief=Messages.config_load_brief)
    async def load(self, ctx):
        """
        Load config from `config.toml`
        """
        load_config()
        await ctx.send(Messages.config_loaded)

    @config.command(name="list", brief=Messages.config_list_brief)
    async def list_all(self, ctx, regex=None):
        if regex is not None:
            try:
                regex = re.compile(regex)
            except re.error as ex:
                await ctx.send(utils.fill_message('config_list_invalid_regex', regex_err=str(ex)))
                return

        keys = dir(config)
        output = "```\n"
        for key in keys[:]:
            if not re.match(r"__.*__", key) and key not in config.config_static:
                if regex is None or regex.match(key) is not None:
                    output += key + "\n"
        output += "```"
        await ctx.send(output)

    @config.command(brief=Messages.config_get_brief)
    async def get(self, ctx, key=None):
        """
        Get value of specified key
        """
        if key is None:
            await ctx.send(utils.get_command_signature(ctx))
            return
        if not hasattr(config, key) or key in config.config_static:
            await ctx.send(Messages.config_wrong_key)
            return
        value = getattr(config, key)
        embed = disnake.Embed(title=key, description=str(value))
        await ctx.send(embed=embed)

    @config.command(brief=Messages.config_backup_brief)
    async def backup(self, ctx):
        """
        Create backup from current config. Backup filename will contain current date.
        """
        config_path = os.path.dirname(__file__)[:-4] + "config/config_backup_"
        config_path += str(datetime.now().date()) + ".toml"
        with open(config_path, "w+", encoding="utf-8") as fd:
            toml.dump(config.toml_dict, fd)
        await ctx.send(Messages.config_backup_created)

    @config.command(brief=Messages.config_sync_template_brief)
    async def sync_template(self, ctx):
        path = os.path.dirname(__file__)[:-4]
        config_path = f"{path}config/config.toml"
        template = toml.load(f"{path}config/config.template.toml", _dict=dict)
        for section in template:
            if section in config.toml_dict:
                for key in template[section]:
                    if key not in config.toml_dict[section]:
                        config.toml_dict[section][key] = template[section][key]
            else:
                config.toml_dict[section] = template[section]
        with open(config_path, "w+", encoding="utf-8") as fd:
            toml.dump(config.toml_dict, fd)
        load_config()
        await ctx.send(Messages.config_synced)

    async def change_value(self, ctx, key: str, value: list, append: bool):
        """
        Changes config atrribute specified by `key` to `value`.
        If `append` values are appended to current setting.
        """
        if not hasattr(config, key) or key in config.config_static:
            await ctx.send(Messages.config_wrong_key)
            return
        config_path = os.path.dirname(__file__)[:-4] + "config/config.toml"
        key_toml = key
        key_split = key.split('_', 1)
        for section in config.toml_dict:
            if key_split[0] == section:
                key_toml = key_split[1]
            if key_toml in config.toml_dict[section]:
                attr = getattr(config, key)
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
                elif isinstance(attr, bool):
                    if value[0].lower() == "false":
                        value = False
                    else:
                        value = True
                elif isinstance(attr, int):
                    try:
                        value = int(value[0])
                    except ValueError:
                        await ctx.send(Messages.config_wrong_type)
                        return
                config.toml_dict[section][key_toml] = value
                break
            else:
                key_toml = key
        else:
            await ctx.send(Messages.config_wrong_key)
            return
        setattr(config, key, value)
        with open(config_path, "w+", encoding="utf-8") as fd:
            toml.dump(config.toml_dict, fd)
        await ctx.send(Messages.config_updated)


def setup(bot):
    bot.add_cog(DynamicConfig(bot))
