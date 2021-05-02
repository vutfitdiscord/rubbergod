import discord
from discord.ext import commands, tasks
from config.app_config import Config
from repository.database import session
from repository.database.verification import Permit, Valid_person
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


def parse_memory(memory):
    parsed = dict()
    for line in memory.strip().splitlines():
        line = line.split()
        login = line[1]
        if login[0] != 'x':
            continue
        last_change = " ".join(line[-3:])
        since_last_change = unchanged_for(last_change, '%b %d %H:%M:%S')
        if since_last_change > 10:
            if login not in parsed:
                parsed[login] = list()
            parsed[login].append(since_last_change)
    return parsed


def parse_semaphores(semaphores):
    parsed = dict()
    parsed_files = dict()
    if "soubory semaforu" in semaphores:
        semaphores, files = semaphores.split("soubory semaforu:\n")
    else:
        files = ""

    for line in semaphores.strip().splitlines():
        line = line.split()
        login = line[1]
        if login[0] != 'x':
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
        if login[0] != 'x':
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
    parsed = dict()
    for line in processes.strip().splitlines():
        line = line.split()
        login = line[0]
        if login[0] != 'x':
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


def insult_login(parsed_items, non_user_format: str, user_format: str, bot, channel, system):
    output_array = []
    for login, array in parsed_items.copy().items():
        user = session.query(Permit).filter(Permit.login == login).one_or_none()
        count = len(array)
        avg_time = float(sum(array)) // count

        person = session.query(Valid_person).filter(Valid_person.login == login).one_or_none()

        if "BIT" not in person.year and "FEKT" not in person.year:
            if login in parsed_items:
                parsed_items.pop(login)
            continue

        if user is None:
            output_array.append(f"{non_user_format.format(system, login)}\n")
        else:
            output_array.append(
                f"""{user_format.format(utils.generate_mention(user.discord_ID), system, str(count),
                                        format_time(avg_time))}\n""")
    return output_array


async def print_output(bot, channel, system, parsed_memory, parsed_semaphores, parsed_files,
                       parsed_processes):
    out_arr = []
    if parsed_memory != dict():
        out_arr.extend(insult_login(parsed_memory,
                                    "Sdílenou paměť na {} nechává nějaký {} co není na serveru.",
                                    "{} máš na {} {} sdílené paměti, ztracené průměrně {}, ty prase.",
                                    bot, channel, system))

    if parsed_semaphores != dict():
        out_arr.extend(insult_login(parsed_semaphores,
                                    "Semafory nechává na {} nějaký {} co není na serveru",
                                    "{} máš na {} {} semaforů, ležících tam průměrně {}, ty prase.",
                                    bot, channel, system))

    if parsed_files != dict():
        for login, array in parsed_files.copy().items():
            user = session.query(Permit). \
                filter(Permit.login == login).one_or_none()
            login_not_in_name = array[1]
            array = array[0]
            count = len(array)
            avg_time = float(sum(array)) // count

            person = session.query(Valid_person). \
                filter(Valid_person.login == login).one_or_none()

            if "BIT" not in person.year and "FEKT" not in person.year:
                if login in parsed_files:
                    parsed_files.pop(login)
                continue

            if user is None:
                out_arr.append(
                    f"Soubory semaforu nechává na {system} nějaký {login} co není na serveru.\n")
            else:
                out_arr.append(
                    f"{utils.generate_mention(user.discord_ID)}" +
                    f"máš na {system}(/dev/shm) {count} souborů semaforu.\n")
                if avg_time > 9:
                    out_arr.append(
                        f"Leží ti tam průměrně už {format_time(avg_time)}, ty prase.\n")
                if login_not_in_name:
                    out_arr.append(
                        "Nemáš v názvu tvůj login, takže můžeš mit kolize s ostatními, ty prase.\n")

    if parsed_processes != dict():
        out_arr.extend(insult_login(parsed_processes,
                                    "Na {} leží procesy nějakého {} co není na serveru.",
                                    "{} máš na {} {} procesů, běžících průměrně {}, ty prase",
                                    bot, channel, system))

    if (parsed_memory == dict() and parsed_semaphores == dict()
            and parsed_processes == dict() and parsed_files == dict()):
        await channel.send("Na " + system + " uklizeno <:HYPERS:493154327318233088>")
    else:
        output_message = ""
        for msg in out_arr:
            tmp_msg = output_message + msg

            # Limit is 2000 chars but we will split it by this weird number to have some headroom
            if len(tmp_msg) >= 1900:
                await channel.send(output_message[:-1])
                output_message = msg
            else:
                output_message = tmp_msg

        if output_message != "":
            await channel.send(output_message[:-1])


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
        output, error = process.communicate()
        memory, rest = output.decode('utf-8').split("semafory:\n")
        semaphores, processes = rest.split("procesy:\n")
        try:
            parsed_memory = parse_memory(memory)
            parsed_semaphores, parsed_files = parse_semaphores(semaphores)
            parsed_processes = parse_processes(processes)
            await print_output(self.bot, channel, "merlinovi", parsed_memory, parsed_semaphores,
                               parsed_files, parsed_processes)
        except IndexError:
            await channel.send("Toastere, máš bordel v parsování.")

        process = subprocess.Popen(["ssh", "eva"], stdout=subprocess.PIPE)
        output = process.communicate()[0]

        memory, rest = output.decode('utf-8').split("semafory:\n")
        semaphores, processes = rest.split("procesy:\n")
        # remove unwanted processes
        processes = filter_processes(processes)
        try:
            parsed_memory = parse_memory(memory)
            parsed_semaphores, _ = parse_semaphores(semaphores)
            parsed_processes = parse_processes(processes)
            await print_output(self.bot, channel, "eve", parsed_memory, parsed_semaphores, dict(),
                               parsed_processes)
        except IndexError:
            await channel.send("Toastere, máš bordel v parsování.")
        # eva doesn't seem to have /dev/shm
        await channel.send("Pokud nevíte jak po sobě uklidit, checkněte: " +
                           "https://discordapp.com/channels/" +
                           "461541385204400138/534431057001316362/" +
                           "698701631495340033")


def setup(bot):
    bot.add_cog(IOS(bot))
