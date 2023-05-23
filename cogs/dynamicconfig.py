"""
Cog for dynamically changing config.
"""

import os
import re
import shlex
from datetime import datetime
from typing import List

import disnake
import toml
from disnake.ext import commands

import utils
from cogs.base import Base
from config.app_config import config, config_get_keys, load_config
from config.messages import Messages
from permissions import permission_check


async def autocomp_keys(inter: disnake.ApplicationCommandInteraction, user_input: str) -> List[str]:
    return [key for key in config_get_keys() if user_input.lower() in key][:25]


class DynamicConfig(Base, commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.check(permission_check.is_bot_admin)
    @commands.slash_command(name="config")
    async def config(self, inter):
        """
        Group of commands for dynamically changing config
        """
        pass

    @config.sub_command(name="set", description=Messages.config_set_brief)
    async def set_value(
        self,
        inter: disnake.ApplicationCommandInteraction,
        key: str = commands.Param(autocomplete=autocomp_keys),
        value: str = commands.Param()
    ):
        """
        Dynamically change config values
        """
        await self.change_value(inter, key, value, False)
        load_config()

    @config.sub_command(description=Messages.config_append_brief)
    async def append(
        self, inter: disnake.ApplicationCommandInteraction,
        key: str = commands.Param(autocomplete=autocomp_keys),
        value: str = commands.Param()
    ):
        """
        Append value(s) to existing config
        For string and int types command has same behaviour as `set_value`.
        """
        await self.change_value(inter, key, value, True)
        load_config()

    @config.sub_command(description=Messages.config_load_brief)
    async def load(self, inter: disnake.ApplicationCommandInteraction):
        """
        Load config from `config.toml`
        """
        load_config()
        await inter.send(Messages.config_loaded)

    @config.sub_command(name="list", description=Messages.config_list_brief)
    async def list_all(self, inter: disnake.ApplicationCommandInteraction, regex: str = None):
        if regex is not None:
            try:
                regex = re.compile(regex)
            except re.error as ex:
                await inter.send(utils.fill_message('config_list_invalid_regex', regex_err=str(ex)))
                return

        output = "```\n"
        for key in config_get_keys()[:]:
            if regex is None or regex.match(key) is not None:
                output += key + "\n"
        output += "```"
        await inter.send(output)

    @config.sub_command(description=Messages.config_get_brief)
    async def get(
        self,
        inter: disnake.ApplicationCommandInteraction,
        key: str = commands.Param(autocomplete=autocomp_keys)
    ):
        """
        Get value of specified key
        """
        if not hasattr(config, key) or key in config.config_static:
            await inter.send(Messages.config_wrong_key)
            return
        value = getattr(config, key)
        embed = disnake.Embed(title=key, description=str(value))
        await inter.send(embed=embed)

    @config.sub_command(description=Messages.config_backup_brief)
    async def backup(self, inter: disnake.ApplicationCommandInteraction):
        """
        Create backup from current config. Backup filename will contain current date.
        """
        config_path = os.path.dirname(__file__)[:-4] + "config/config_backup_"
        config_path += str(datetime.now().date()) + ".toml"
        with open(config_path, "w+", encoding="utf-8") as fd:
            toml.dump(config.toml_dict, fd)
        await inter.send(Messages.config_backup_created)

    @config.sub_command(description=Messages.config_sync_template_brief)
    async def update(self, inter: disnake.ApplicationCommandInteraction):
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
        await inter.send(Messages.config_updated)

    async def change_value(
        self,
        inter: disnake.ApplicationCommandInteraction,
        key: str,
        value: str,
        append: bool
    ):
        """
        Changes config atrribute specified by `key` to `value`.
        If `append` values are appended to current setting.
        """
        if not hasattr(config, key) or key in config.config_static:
            await inter.send(Messages.config_wrong_key)
            return
        try:
            value = shlex.split(value)
        except Exception as e:
            await inter.send(e)
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
                                await inter.send(Messages.config_wrong_type)
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
                        await inter.send(Messages.config_wrong_type)
                        return
                config.toml_dict[section][key_toml] = value
                break
            else:
                key_toml = key
        else:
            await inter.send(Messages.config_wrong_key)
            return
        setattr(config, key, value)
        with open(config_path, "w+", encoding="utf-8") as fd:
            toml.dump(config.toml_dict, fd)
        await inter.send(Messages.config_updated)


def setup(bot):
    bot.add_cog(DynamicConfig(bot))
