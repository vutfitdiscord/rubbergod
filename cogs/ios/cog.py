"""
Cog for the IOS subject. Get users on merlin/eva server which have blocking processes running.
"""

import subprocess

import disnake
from disnake.ext import commands, tasks

from cogs.base import Base
from permissions import permission_check
from rubbergod import Rubbergod
from utils import cooldowns

from . import features
from .messages_cz import MessagesCZ


class IOS(Base, commands.Cog):
    def __init__(self, bot: Rubbergod):
        super().__init__()
        self.bot = bot
        self.tasks = [self.ios_task]

    @cooldowns.default_cooldown
    @commands.check(permission_check.helper_plus)
    @commands.slash_command(name="ios", description=MessagesCZ.ios_brief, guild_ids=[Base.config.guild_id])
    async def ios(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        await self.ios_task(inter)

    @commands.slash_command(name="ios_task", guild_ids=[Base.config.guild_id])
    async def _ios(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @commands.check(permission_check.is_bot_admin)
    @_ios.sub_command(name="start", description=MessagesCZ.task_start_brief)
    async def ios_task_start(self, inter: disnake.ApplicationCommandInteraction):
        try:
            self.ios_task.start()
            await inter.send(MessagesCZ.task_start_success)
        except RuntimeError:
            await inter.send(MessagesCZ.task_start_already_set)

    @commands.check(permission_check.is_bot_admin)
    @_ios.sub_command(name="stop", description=MessagesCZ.task_stop_brief)
    async def ios_task_stop(self, inter: disnake.ApplicationCommandInteraction):
        if self.ios_task.is_running():
            self.ios_task.stop()
            await inter.send(MessagesCZ.task_stop_success)
        else:
            await inter.send(MessagesCZ.task_nothing_to_stop)

    @commands.check(permission_check.is_bot_admin)
    @_ios.sub_command(name="cancel", description=MessagesCZ.task_cancel_brief)
    async def ios_task_cancel(self, inter: disnake.ApplicationCommandInteraction):
        if self.ios_task.is_running():
            self.ios_task.cancel()
            await inter.send(MessagesCZ.task_stop_success)
        else:
            await inter.send(MessagesCZ.task_nothing_to_stop)

    @tasks.loop(minutes=Base.config.ios_looptime_minutes)
    async def ios_task(self, inter: disnake.ApplicationCommandInteraction = None):
        # Respond to interaction if any, else print everything to #ios-private
        channel = inter.channel if inter is not None else self.bot.get_channel(self.config.ios_channel_id)
        if inter is not None:
            await inter.edit_original_response(MessagesCZ.howto_clean)
        else:
            await channel.send(MessagesCZ.howto_clean)

        process = subprocess.Popen(
            ["ssh", "-i", self.config.ios_leakcheck_key_path, "merlin"], stdout=subprocess.PIPE
        )
        output, _ = process.communicate()

        try:
            memory, rest = output.decode("utf-8").split("semafory:\n")
        except ValueError:
            await channel.send(MessagesCZ.connection_error(system="merlinovi"))
            return
        semaphores, processes = rest.split("procesy:\n")
        try:
            parsed_memory = features.parse_memory(memory)
            parsed_semaphores, parsed_files = features.parse_semaphores(semaphores)
            parsed_processes = features.parse_processes(processes)
            parsed_resources = {
                features.RESOURCE_TYPE.MEMORY: parsed_memory,
                features.RESOURCE_TYPE.SEMAPHORE: parsed_semaphores,
                features.RESOURCE_TYPE.FILE: parsed_files,
                features.RESOURCE_TYPE.PROCESS: parsed_processes,
            }
            await features.print_output(channel, "merlinovi", features.filter_year(parsed_resources))
        except (IndexError, ValueError) as e:
            await channel.send(MessagesCZ.parsing_error)
            # Send it to bot-dev channel anyway
            raise e

        process = subprocess.Popen(
            ["ssh", "-i", self.config.ios_leakcheck_key_path, "eva"], stdout=subprocess.PIPE
        )
        output, _ = process.communicate()
        try:
            memory, rest = output.decode("utf-8").split("semafory:\n")
        except ValueError:
            await channel.send(MessagesCZ.connection_error(system="evě"))
            return
        semaphores, processes = rest.split("procesy:\n")
        # remove unwanted processes
        processes = features.filter_processes(processes)
        try:
            parsed_memory = features.parse_memory(memory)
            parsed_semaphores, _ = features.parse_semaphores(semaphores)
            parsed_processes = features.parse_processes(processes)
            parsed_resources = {
                features.RESOURCE_TYPE.MEMORY: parsed_memory,
                features.RESOURCE_TYPE.SEMAPHORE: parsed_semaphores,
                features.RESOURCE_TYPE.PROCESS: parsed_processes,
            }
            await features.print_output(channel, "evě", features.filter_year(parsed_resources))
        except (IndexError, ValueError) as e:
            await channel.send(MessagesCZ.parsing_error)
            # Send it to bot-dev channel anyway
            raise e
        # eva doesn't seem to have /dev/shm
