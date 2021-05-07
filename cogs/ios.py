import discord
from discord.ext import commands, tasks
from config.app_config import Config
from repository.database import session
from repository.database.verification import Permit, Valid_person
from features.list_message_sender import send_list_of_messages
import utils
import subprocess
import datetime
import re


def running_for(time):
    now = datetime.datetime.now()
    time = time.split(':')
    if len(time) == 2:
        hours = now.hour - int(time[0])
        minutes = now.minute - int(time[1])
        return hours * 60 + minutes
    else:
        date = datetime.datetime.strptime(time[0], "%b%d")
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
        login: session.query(Valid_person).filter(Valid_person.login == login).one_or_none()
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

    if weeks >= 1:
        return f"{round(weeks, 1)} týdnů"
    elif days >= 1:
        return f"{round(days, 1)} dní"
    elif hours >= 1:
        return f"{round(hours, 1)} hodin"
    return f"{round(minutes, 1)} minut"


class RESOURCE_TYPE:
    MEMORY      = 'MEMORY'
    SEMAPHORE   = 'SEMAPHORE'
    PROCESS     = 'PROCESS'
    FILE        = 'FILE'

# inflected resource names to match the czech language
_inflected_resources = {
    RESOURCE_TYPE.MEMORY:   ('sdílená paměť', 'sdílené paměti', 'ztracené'),
    RESOURCE_TYPE.SEMAPHORE:('semafory',      'semaforů',       'ležících'),
    RESOURCE_TYPE.PROCESS:  ('procesy',       'procesů',        'běžících'),
}
def insult_login(parsed_items, system, res_type):
    output_array = []
    for login, array in parsed_items.items():
        user = session.query(Permit).filter(Permit.login == login).one_or_none()

        if False:
            msg = f"Na {system} leží {_inflected_resources[res_type][0]} nějakého `{login}` co není na serveru."
        else:
            count = len(array)
            avg_time = int(sum(array) // count)

            msg = ((f"{utils.generate_mention(user.discord_ID)}" if user else "@MENTION") +f" máš na {system} `{count}` {_inflected_resources[res_type][1]}, "
                   f"{_inflected_resources[res_type][2]} průměrně `{format_time(avg_time)}`, ty prase")
        output_array += [msg]
    return output_array

def insult_login_shm(parsed_files, system):
    output_array = []
    for login, data in parsed_files.items():
        user = session.query(Permit).filter(Permit.login == login).one_or_none()
        array, login_not_in_name = data

        if False:
            msg = f"Na {system} leží soubory semaforů nějakého `{login}` co není na serveru."
        else:
            count = len(array)
            avg_time = float(sum(array)) // count

            msg = (
                (f"{utils.generate_mention(user.discord_ID)} " if user else "@MENTION ")+
                f"máš na {system}(`/dev/shm`) `{count}` souborů semaforů.")
            if avg_time > 9:
                msg += f"\n        Leží ti tam průměrně už `{format_time(avg_time)}`, ty prase."
            if login_not_in_name:
                msg += "\n        Nemáš v názvu tvůj login, takže můžeš mit kolize s ostatními, ty prase."
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


class IOS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.cooldown(rate=5, per=30.0, type=commands.BucketType.user)
    @commands.check(utils.helper_plus)
    @commands.command()
    async def ios(self, ctx):
        await self.ios_body(ctx.channel)

    @commands.check(utils.is_bot_admin)
    @commands.command()
    async def ios_start(self, ctx):
        self.ios_body.start(ctx.channel)

    @commands.check(utils.is_bot_admin)
    @commands.command()
    async def ios_stop(self, ctx):
        self.ios_body.stop()

    @commands.check(utils.is_bot_admin)
    @commands.command()
    async def ios_cancel(self, ctx):
        self.ios_body.cancel()

    @tasks.loop(minutes=Config.ios_looptime_minutes)
    async def ios_body(self, channel=discord.Object(id='534431057001316362')):
        process = subprocess.Popen(["ssh", "merlin"], stdout=subprocess.PIPE)
        output, _ = process.communicate()
        memory, rest = output.decode('utf-8').split("semafory:\n")
        semaphores, processes = rest.split("procesy:\n")
        try:
            parsed_memory = parse_memory(memory)
            parsed_semaphores, parsed_files = parse_semaphores(semaphores)
            parsed_processes = parse_processes(processes)
            parsed_resources = {
                RESOURCE_TYPE.MEMORY:   parsed_memory,
                RESOURCE_TYPE.SEMAPHORE:parsed_semaphores,
                RESOURCE_TYPE.FILE:     parsed_files,
                RESOURCE_TYPE.PROCESS:  parsed_processes,
            }
            await print_output(self.bot, channel, "merlinovi", filter_year(parsed_resources))
        except IndexError:
            await channel.send("Toastere, máš bordel v parsování.")

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
                RESOURCE_TYPE.MEMORY:   parsed_memory,
                RESOURCE_TYPE.SEMAPHORE:parsed_semaphores,
                RESOURCE_TYPE.PROCESS:  parsed_processes,
            }
            await print_output(self.bot, channel, "evě", filter_year(parsed_resources))
        except IndexError:
            await channel.send("Toastere, máš bordel v parsování.")
        # eva doesn't seem to have /dev/shm
        await channel.send("Pokud nevíte jak po sobě uklidit, checkněte: " +
                           "https://discordapp.com/channels/" +
                           "461541385204400138/534431057001316362/" +
                           "698701631495340033")


def setup(bot):
    bot.add_cog(IOS(bot))
