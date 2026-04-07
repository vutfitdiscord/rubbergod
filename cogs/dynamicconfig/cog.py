"""
Cog for dynamically changing config.
"""

import re
import shlex
from typing import Any

import disnake
import toml
from disnake.ext import commands

from cogs.base import Base
from config.app_config import CONFIG_PATH, config_get_keys, load_config
from rubbergod import Rubbergod
from utils.checks import PermissionsCheck

from .messages_cz import MessagesCZ


async def autocomp_keys(inter: disnake.ApplicationCommandInteraction, user_input: str) -> list[str]:
    return [key for key in config_get_keys() if user_input.lower() in key][:25]


class DynamicConfig(Base, commands.Cog):
    def __init__(self, bot: Rubbergod):
        super().__init__()
        self.bot = bot

    @PermissionsCheck.is_bot_admin()
    @commands.slash_command(name="config")
    async def config_cmd(self, inter: disnake.ApplicationCommandInteraction):
        """
        Group of commands for dynamically changing config
        """
        pass

    @config_cmd.sub_command(name="set", description=MessagesCZ.set_brief)
    async def set_value(
        self,
        inter: disnake.ApplicationCommandInteraction,
        key: str = commands.Param(autocomplete=autocomp_keys),
        value: str = commands.Param(),
    ):
        """
        Dynamically change config values
        """
        await self.change_value(inter, key, value, False)
        load_config()

    @config_cmd.sub_command(description=MessagesCZ.append_brief)
    async def append(
        self,
        inter: disnake.ApplicationCommandInteraction,
        key: str = commands.Param(autocomplete=autocomp_keys),
        value: str = commands.Param(),
    ):
        """
        Append value(s) to existing config
        For string and int types command has same behaviour as `set_value`.
        """
        await self.change_value(inter, key, value, True)
        load_config()

    @config_cmd.sub_command(description=MessagesCZ.remove_brief)
    async def remove(
        self,
        inter: disnake.ApplicationCommandInteraction,
        key: str = commands.Param(autocomplete=autocomp_keys),
        value: str = commands.Param(),
    ):
        """
        Remove value(s) from existing config list
        Only works on list type config values.
        """
        await self.remove_value(inter, key, value)
        load_config()

    @config_cmd.sub_command(description=MessagesCZ.load_brief)
    async def load(self, inter: disnake.ApplicationCommandInteraction):
        """
        Load config from `config.toml`
        """
        load_config()
        await inter.send(MessagesCZ.config_loaded)

    @config_cmd.sub_command(name="list", description=MessagesCZ.list_brief)
    async def list_all(self, inter: disnake.ApplicationCommandInteraction, regex: str = None):
        if regex is not None:
            try:
                regex_pat = re.compile(regex)
            except re.error as ex:
                await inter.send(MessagesCZ.list_invalid_regex(regex_err=str(ex)))
                return

        output = "```\n"
        for key in config_get_keys()[:]:
            if regex_pat is None or regex_pat.match(key) is not None:
                output += key + "\n"
        output += "```"
        await inter.send(output)

    @config_cmd.sub_command(description=MessagesCZ.get_brief)
    async def get(
        self,
        inter: disnake.ApplicationCommandInteraction,
        key: str = commands.Param(autocomplete=autocomp_keys),
    ):
        """
        Get value of specified key
        """
        if not hasattr(self.config, key) or key in self.config.config_static:
            await inter.send(MessagesCZ.wrong_key)
            return
        value = getattr(self.config, key)
        embed = disnake.Embed(title=key, description=str(value))
        await inter.send(embed=embed)

    @config_cmd.sub_command(description=MessagesCZ.sync_template_brief)
    async def update(self, inter: disnake.ApplicationCommandInteraction):
        template_path = CONFIG_PATH.parent.joinpath("config.template.toml")
        template = toml.load(template_path, _dict=dict)
        for section in template:
            if section in self.config.toml_dict:
                for key in template[section]:
                    if key not in self.config.toml_dict[section]:
                        self.config.toml_dict[section][key] = template[section][key]
            else:
                self.config.toml_dict[section] = template[section]
        with open(CONFIG_PATH, "w+", encoding="utf-8") as fd:
            toml.dump(self.config.toml_dict, fd)
        load_config()
        await inter.send(MessagesCZ.config_updated)

    async def change_value(
        self, inter: disnake.ApplicationCommandInteraction, key: str, value: str, append: bool
    ):
        """
        Changes config attribute specified by `key` to `value`.
        If `append` values are appended to current setting.
        """
        if not hasattr(self.config, key) or key in self.config.config_static:
            await inter.send(MessagesCZ.wrong_key)
            return
        try:
            new_val: Any = shlex.split(value)
        except Exception as e:
            await inter.send(e)
            return
        key_toml = key
        key_split = key.split("_", 1)
        for section in self.config.toml_dict:
            if key_split[0] == section:
                key_toml = key_split[1]
            if key_toml in self.config.toml_dict[section]:
                attr = getattr(self.config, key)
                if isinstance(attr, list):
                    if isinstance(attr[0], int):
                        for idx, item in enumerate(new_val):
                            try:
                                new_val[idx] = int(item)
                            except ValueError:
                                await inter.send(MessagesCZ.wrong_type)
                                return
                    if append:
                        new_val = attr + new_val
                elif isinstance(attr, tuple) and append:
                    new_val = tuple(list(attr) + new_val)
                elif isinstance(attr, str):
                    new_val = " ".join(new_val)
                elif isinstance(attr, bool):
                    if new_val[0].lower() == "false":
                        new_val = False
                    else:
                        new_val = True
                elif isinstance(attr, int):
                    try:
                        new_val = int(new_val[0])
                    except ValueError:
                        await inter.send(MessagesCZ.wrong_type)
                        return
                self.config.toml_dict[section][key_toml] = new_val
                break
            else:
                key_toml = key
        else:
            await inter.send(MessagesCZ.wrong_key)
            return
        setattr(self.config, key, new_val)
        with open(CONFIG_PATH, "w+", encoding="utf-8") as fd:
            toml.dump(self.config.toml_dict, fd)
        await inter.send(MessagesCZ.config_updated)

    async def remove_value(self, inter: disnake.ApplicationCommandInteraction, key: str, value: str):
        """
        Removes value(s) from a list in config attribute specified by `key`.
        Only works on list type config values.
        """
        if not hasattr(self.config, key) or key in self.config.config_static:
            await inter.send(MessagesCZ.wrong_key)
            return

        attr = getattr(self.config, key)
        if not isinstance(attr, list):
            await inter.send(MessagesCZ.not_a_list)
            return

        try:
            values_to_remove: Any = shlex.split(value)
        except Exception as e:
            await inter.send(e)
            return

        # Convert values_to_remove to the correct type if the list contains ints
        if len(attr) > 0 and isinstance(attr[0], int):
            for idx, item in enumerate(values_to_remove):
                try:
                    values_to_remove[idx] = int(item)
                except ValueError:
                    await inter.send(MessagesCZ.wrong_type)
                    return

        # Remove the values from the list
        new_val = attr.copy()
        removed_any = False
        for val in values_to_remove:
            if val in new_val:
                new_val.remove(val)
                removed_any = True

        if not removed_any:
            await inter.send(MessagesCZ.value_not_found)
            return

        # Find the correct section in toml_dict and update it
        key_toml = key
        key_split = key.split("_", 1)
        for section in self.config.toml_dict:
            if key_split[0] == section:
                key_toml = key_split[1]
            if key_toml in self.config.toml_dict[section]:
                self.config.toml_dict[section][key_toml] = new_val
                break
            else:
                key_toml = key
        else:
            await inter.send(MessagesCZ.wrong_key)
            return

        setattr(self.config, key, new_val)
        with open(CONFIG_PATH, "w+", encoding="utf-8") as fd:
            toml.dump(self.config.toml_dict, fd)
        await inter.send(MessagesCZ.config_updated)
