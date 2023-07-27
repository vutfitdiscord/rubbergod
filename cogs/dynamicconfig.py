"""
Cog for dynamically changing config.
"""

import re
import shlex
from datetime import datetime
from pathlib import Path
from typing import List

import disnake
import toml
from disnake.ext import commands

from cogs.base import Base
from config.app_config import config_get_keys, load_config
from config.messages import Messages
from permissions import permission_check


async def autocomp_keys(inter: disnake.ApplicationCommandInteraction, user_input: str) -> List[str]:
    return [key for key in config_get_keys() if user_input.lower() in key][:25]


class DynamicConfig(Base, commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        # /rubbergod/cogs/dynamicconfig.py -> /rubbergod/config
        self.config_dir = Path(__file__).parent.parent.joinpath("config")
        self.config_path = self.config_dir.joinpath("config.toml")

    @commands.check(permission_check.is_bot_admin)
    @commands.slash_command(name="config")
    async def config_cmd(self, inter):
        """
        Group of commands for dynamically changing config
        """
        pass

    @config_cmd.sub_command(name="set", description=Messages.config_set_brief)
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

    @config_cmd.sub_command(description=Messages.config_append_brief)
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

    @config_cmd.sub_command(description=Messages.config_load_brief)
    async def load(self, inter: disnake.ApplicationCommandInteraction):
        """
        Load config from `config.toml`
        """
        load_config()
        await inter.send(Messages.config_loaded)

    @config_cmd.sub_command(name="list", description=Messages.config_list_brief)
    async def list_all(self, inter: disnake.ApplicationCommandInteraction, regex: str = None):
        if regex is not None:
            try:
                regex = re.compile(regex)
            except re.error as ex:
                await inter.send(Messages.config_list_invalid_regex(regex_err=str(ex)))
                return

        output = "```\n"
        for key in config_get_keys()[:]:
            if regex is None or regex.match(key) is not None:
                output += key + "\n"
        output += "```"
        await inter.send(output)

    @config_cmd.sub_command(description=Messages.config_get_brief)
    async def get(
        self,
        inter: disnake.ApplicationCommandInteraction,
        key: str = commands.Param(autocomplete=autocomp_keys)
    ):
        """
        Get value of specified key
        """
        if not hasattr(self.config, key) or key in self.config.config_static:
            await inter.send(Messages.config_wrong_key)
            return
        value = getattr(self.config, key)
        embed = disnake.Embed(title=key, description=str(value))
        await inter.send(embed=embed)

    @config_cmd.sub_command(description=Messages.config_backup_brief)
    async def backup(self, inter: disnake.ApplicationCommandInteraction):
        """
        Create backup from current config. Backup filename will contain current date.
        """
        date = datetime.today()
        backup_path = self.config_dir.joinpath(f"config_backup_{date}.toml")
        with open(backup_path, "w+", encoding="utf-8") as fd:
            toml.dump(self.config.toml_dict, fd)
        await inter.send(Messages.config_backup_created)

    @config_cmd.sub_command(description=Messages.config_sync_template_brief)
    async def update(self, inter: disnake.ApplicationCommandInteraction):
        template_path = self.config_dir.joinpath("config.template.toml")
        template = toml.load(template_path, _dict=dict)
        for section in template:
            if section in self.config.toml_dict:
                for key in template[section]:
                    if key not in self.config.toml_dict[section]:
                        self.config.toml_dict[section][key] = template[section][key]
            else:
                self.config.toml_dict[section] = template[section]
        with open(self.config_path, "w+", encoding="utf-8") as fd:
            toml.dump(self.config.toml_dict, fd)
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
        if not hasattr(self.config, key) or key in self.config.config_static:
            await inter.send(Messages.config_wrong_key)
            return
        try:
            value = shlex.split(value)
        except Exception as e:
            await inter.send(e)
            return
        key_toml = key
        key_split = key.split('_', 1)
        for section in self.config.toml_dict:
            if key_split[0] == section:
                key_toml = key_split[1]
            if key_toml in self.config.toml_dict[section]:
                attr = getattr(self.config, key)
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
                self.config.toml_dict[section][key_toml] = value
                break
            else:
                key_toml = key
        else:
            await inter.send(Messages.config_wrong_key)
            return
        setattr(self.config, key, value)
        with open(self.config_path, "w+", encoding="utf-8") as fd:
            toml.dump(self.config.toml_dict, fd)
        await inter.send(Messages.config_updated)


def setup(bot):
    bot.add_cog(DynamicConfig(bot))
