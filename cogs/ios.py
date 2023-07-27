"""
Cog for the IOS subject. Get users on merlin/eva server which have blocking processes running.
"""

import datetime
import re
import subprocess

import disnake
from disnake.ext import commands, tasks

import utils
from cogs.base import Base
from config import cooldowns
from config.messages import Messages
from database import session
from database.verification import PermitDB, ValidPersonDB
from features.list_message_sender import send_list_of_messages
from permissions import permission_check


def running_for(time):
    now = datetime.datetime.now()
    time = time.split(':')
    if len(time) == 2:
        hours = now.hour - int(time[0])
        minutes = now.minute - int(time[1])
        return hours * 60 + minutes
    else:
        try:
            date = datetime.datetime.strptime(time[0], "%b%d")
        except ValueError:
            date = datetime.datetime.strptime(time[0], "%a%d")
            date = date.replace(year=now.year, month=now.month)
        minutes = (now - date.replace(year=now.year)).total_seconds() // 60
        # subtracting a day as to assume it was ran right before midnight
        return minutes - 1440


def unchanged_for(date, format_str):
    now = datetime.datetime.now()
    date = datetime.datetime.strptime(date, format_str)
    return (now - date.replace(year=now.year)).total_seconds() // 60


# filter people and keep only those containing "BIT" or "FEKT" in person.year
def filter_year(resources):
    # get unique logins and people objects from db
    logins = set(login for res_data in resources.values() for login in res_data.keys())
    people = {
        login: session.query(ValidPersonDB).filter(ValidPersonDB.login == login).one_or_none()
        for login in logins
    }

    # keep only people with "BIT" or "FEKT" in their person.year
    out_res = {res_type: {} for res_type in resources.keys()}
    for res_type, res_data in resources.items():
        for login, data in res_data.items():
            if not people.get(login) or "BIT" in people[login].year or "FEKT" in people[login].year:
                out_res[res_type][login] = data
    return out_res


def parse_memory(memory):
    parsed = {}
    for line in memory.strip().splitlines():
        line = line.split()
        login = line[1]
        if not login.startswith('x'):
            continue
        last_change = " ".join(line[-3:])
        since_last_change = unchanged_for(last_change, '%b %d %H:%M:%S')
        if since_last_change > 10:
            if login not in parsed:
                parsed[login] = list()
            parsed[login].append(since_last_change)
    return parsed


def parse_semaphores(semaphores):
    parsed = {}
    parsed_files = {}
    if "soubory semaforu" in semaphores:
        semaphores, files = semaphores.split("soubory semaforu:\n")
    else:
        files = ""

    for line in semaphores.strip().splitlines():
        line = line.split()
        login = line[1]
        if not login.startswith('x'):
            continue
        last_change = " ".join(line[-4:-1])
        since_last_change = unchanged_for(last_change, '%b %d %H:%M:%S')
        if since_last_change > 10:
            if login not in parsed:
                parsed[login] = list()
            parsed[login].append(since_last_change)

    for line in files.strip().splitlines():
        line = line.split()
        login = line[2]
        if not login.startswith('x'):
            continue
        last_change = " ".join(line[5:7])
        name = line[7]
        since_last_change = unchanged_for(last_change, "%m-%d %H:%M")
        if since_last_change > 10 or login not in name:
            if login not in parsed_files:
                parsed_files[login] = [list(), False]
            parsed_files[login][0].append(since_last_change)
            if login not in name:
                parsed_files[login][1] = True

    return parsed, parsed_files


def parse_processes(processes):
    parsed = {}
    for line in processes.strip().splitlines():
        line = line.split()
        login = line[0]
        if not login.startswith('x'):
            continue
        time = line[8]
        uptime = running_for(time)
        if uptime > 10:
            if login not in parsed:
                parsed[login] = list()
            parsed[login].append(uptime)
    return parsed


def filter_processes(processes):
    out = []
    for line in processes.strip().splitlines():
        if re.search(r"/[a-zA-Z0-9.]+ \d+ \d+ \d+ \d+ \d+$", line):
            out.append(line)
    return "\n".join(out)


def format_time(minutes):
    hours = minutes / 60
    days = hours / 24
    weeks = days / 7
    months = days / 30
    years = months / 12

    if years >= 1:
        return f"{round(years, 1)} roků"
    elif months >= 1:
        return f"{round(months, 1)} měsíců"
    elif weeks >= 1:
        return f"{round(weeks, 1)} týdnů"
    elif days >= 1:
        return f"{round(days, 1)} dní"
    elif hours >= 1:
        return f"{round(hours, 1)} hodin"
    return f"{round(minutes, 1)} minut"


class RESOURCE_TYPE:
    MEMORY = 'MEMORY'
    SEMAPHORE = 'SEMAPHORE'
    PROCESS = 'PROCESS'
    FILE = 'FILE'


# inflected resource names to match the czech language
_inflected_resources = {
    RESOURCE_TYPE.MEMORY:    ('sdílená paměť', 'sdílené paměti', 'ztracené'),
    RESOURCE_TYPE.SEMAPHORE: ('semafory',      'semaforů',       'ležících'),
    RESOURCE_TYPE.PROCESS:   ('procesy',       'procesů',        'běžících'),
}


def insult_login(parsed_items, system, res_type):
    output_array = []
    for login, array in parsed_items.items():
        user = session.query(PermitDB).filter(PermitDB.login == login).one_or_none()

        if not user:
            msg = f"Na {system} leží {_inflected_resources[res_type][0]} " \
                f"nějakého `{login}`, co není na serveru."
        else:
            count = len(array)
            avg_time = int(sum(array) // count)

            msg = (
                f"{utils.generate_mention(user.discord_ID)} máš na "
                f"{system} `{count}` {_inflected_resources[res_type][1]}, "
                f"{_inflected_resources[res_type][2]} průměrně `{format_time(avg_time)}`, ty prase."
            )
        output_array += [msg]
    return output_array


def insult_login_shm(parsed_files, system):
    output_array = []
    for login, data in parsed_files.items():
        user = session.query(PermitDB).filter(PermitDB.login == login).one_or_none()
        array, login_not_in_name = data

        if not user:
            msg = f"Na {system} leží soubory semaforů nějakého `{login}`, co není na serveru."
        else:
            count = len(array)
            avg_time = float(sum(array)) // count

            msg = (
                f"{utils.generate_mention(user.discord_ID)} "
                f"máš na {system} (`/dev/shm`) `{count}` souborů semaforů.")
            if avg_time > 9:
                msg += f"\n\t\tLeží ti tam průměrně už `{format_time(avg_time)}`, ty prase."
            if login_not_in_name:
                msg += "\n\t\tNemáš v názvu tvůj login, takže můžeš mit kolize s ostatními, ty prase."
        output_array += [msg]
    return output_array


async def print_output(bot, channel, system, resources):
    out_arr = []
    for res_type in [RESOURCE_TYPE.MEMORY, RESOURCE_TYPE.SEMAPHORE, RESOURCE_TYPE.PROCESS]:
        if resources.get(res_type):
            out_arr += insult_login(resources[res_type], system, res_type)
    if (shm_resources := resources.get(RESOURCE_TYPE.FILE)):
        out_arr += insult_login_shm(shm_resources, system)

    if not any(resources.values()):
        await channel.send(f"Na {system} uklizeno <:HYPERS:493154327318233088>")
    else:
        await send_list_of_messages(channel, out_arr)


class IOS(Base, commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.tasks = [self.ios_task]

    @cooldowns.default_cooldown
    @commands.check(permission_check.helper_plus)
    @commands.slash_command(name="ios", description=Messages.ios_brief, guild_ids=[Base.config.guild_id])
    async def ios(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        await self.ios_task(inter)

    @commands.slash_command(name="ios_task", guild_ids=[Base.config.guild_id])
    async def _ios(self, inter):
        pass

    @commands.check(permission_check.is_bot_admin)
    @_ios.sub_command(name="start", description=Messages.ios_task_start_brief)
    async def ios_task_start(self, inter: disnake.ApplicationCommandInteraction):
        try:
            self.ios_task.start()
            await inter.send(Messages.ios_task_start_success)
        except RuntimeError:
            await inter.send(Messages.ios_task_start_already_set)

    @commands.check(permission_check.is_bot_admin)
    @_ios.sub_command(name="stop", description=Messages.ios_task_stop_brief)
    async def ios_task_stop(self, inter: disnake.ApplicationCommandInteraction):
        if self.ios_task.is_running():
            self.ios_task.stop()
            await inter.send(Messages.ios_task_stop_success)
        else:
            await inter.send(Messages.ios_task_stop_nothing_to_stop)

    @commands.check(permission_check.is_bot_admin)
    @_ios.sub_command(name="cancel", description=Messages.ios_task_cancel_brief)
    async def ios_task_cancel(self, inter: disnake.ApplicationCommandInteraction):
        if self.ios_task.is_running():
            self.ios_task.cancel()
            await inter.send(Messages.ios_task_stop_success)
        else:
            await inter.send(Messages.ios_task_stop_nothing_to_stop)

    @tasks.loop(minutes=Base.config.ios_looptime_minutes)
    async def ios_task(self, inter: disnake.ApplicationCommandInteraction = None):
        # Respond to interaction if any, else print everything to #ios
        channel = inter.channel if inter is not None else self.bot.get_channel(self.config.ios_channel_id)
        if inter is not None:
            await inter.edit_original_response(Messages.ios_howto_clean)
        else:
            await channel.send(Messages.ios_howto_clean)

        process = subprocess.Popen(["ssh", "merlin"], stdout=subprocess.PIPE)
        output, _ = process.communicate()
        memory, rest = output.decode('utf-8').split("semafory:\n")
        semaphores, processes = rest.split("procesy:\n")
        try:
            parsed_memory = parse_memory(memory)
            parsed_semaphores, parsed_files = parse_semaphores(semaphores)
            parsed_processes = parse_processes(processes)
            parsed_resources = {
                RESOURCE_TYPE.MEMORY:    parsed_memory,
                RESOURCE_TYPE.SEMAPHORE: parsed_semaphores,
                RESOURCE_TYPE.FILE:      parsed_files,
                RESOURCE_TYPE.PROCESS:   parsed_processes,
            }
            await print_output(self.bot, channel, "merlinovi", filter_year(parsed_resources))
        except (IndexError, ValueError) as e:
            await channel.send(Messages.ios_parsing_error)
            # Send it to bot-dev channel anyway
            raise e

        process = subprocess.Popen(["ssh", "eva"], stdout=subprocess.PIPE)
        output, _ = process.communicate()

        memory, rest = output.decode('utf-8').split("semafory:\n")
        semaphores, processes = rest.split("procesy:\n")
        # remove unwanted processes
        processes = filter_processes(processes)
        try:
            parsed_memory = parse_memory(memory)
            parsed_semaphores, _ = parse_semaphores(semaphores)
            parsed_processes = parse_processes(processes)
            parsed_resources = {
                RESOURCE_TYPE.MEMORY:    parsed_memory,
                RESOURCE_TYPE.SEMAPHORE: parsed_semaphores,
                RESOURCE_TYPE.PROCESS:   parsed_processes,
            }
            await print_output(self.bot, channel, "evě", filter_year(parsed_resources))
        except (IndexError, ValueError) as e:
            await channel.send(Messages.ios_parsing_error)
            # Send it to bot-dev channel anyway
            raise e
        # eva doesn't seem to have /dev/shm


def setup(bot):
    bot.add_cog(IOS(bot))
