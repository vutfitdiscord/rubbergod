from discord import Member
from discord.ext import commands
from config import config, messages
from repository.database import session
from repository.database.verification import Permit, Valid_person
import discord
import utils
import subprocess
import datetime
import re


config = config.Config
Messages = messages.Messages


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
        if re.search("/[a-zA-Z0-9.]+ \d+ \d+ \d+ \d+ \d+$", line):
            out.append(line)
    return "\n".join(out)


async def print_output(ctx, system, parsed_memory, parsed_semaphores, parsed_files, parsed_processes):
    if parsed_memory != dict():
        for login, array in parsed_memory.copy().items():
            user = session.query(Permit).\
                filter(Permit.login == login).one_or_none()
            count = len(array)
            avg_time = sum(array) // count

            person = session.query(Valid_person).\
                filter(Valid_person.login == login).one_or_none()

            if "BIT" not in person.year and "FEKT" not in person.year:
                if login in parsed_memory:
                    parsed_memory.pop(login)
                continue

            if user is None:
                await ctx.send("Sdilenou pamet nechava nejaky " + login +
                               " co neni na serveru")
            else:
                await ctx.send(utils.generate_mention(user.discord_ID) +
                               " mas na " + system + " " + str(count) +
                               " sdilene pameti, ztracene prumerne " +
                               str(avg_time) + " minut, ty prase")

    if parsed_semaphores != dict():
        for login, array in parsed_semaphores.copy().items():
            user = session.query(Permit).\
                filter(Permit.login == login).one_or_none()
            count = len(array)
            avg_time = sum(array) // count

            person = session.query(Valid_person).\
                filter(Valid_person.login == login).one_or_none()

            if "BIT" not in person.year and "FEKT" not in person.year:
                if login in parsed_semaphores:
                    parsed_semaphores.pop(login)
                continue

            if user is None:
                await ctx.send("Semafory nechava nejaky " + login + " co neni na serveru")
            else:
                await ctx.send(utils.generate_mention(user.discord_ID) +
                               " mas na " + system + " " + str(count) +
                               " semaforu, lezicich tam prumerne " +
                               str(avg_time) + " minut, ty prase")

    if parsed_files != dict():
        for login, array in parsed_files.copy().items():
            user = session.query(Permit).\
                filter(Permit.login == login).one_or_none()
            login_not_in_name = array[1]
            array = array[0]
            count = len(array)
            avg_time = sum(array) // count

            person = session.query(Valid_person).\
                filter(Valid_person.login == login).one_or_none()

            if "BIT" not in person.year and "FEKT" not in person.year:
                if login in parsed_files:
                    parsed_files.pop(login)
                continue

            if user is None:
                await ctx.send("Soubory semaforu nechava nejaky " +
                               login + " co neni na serveru")
            else:
                await ctx.send(utils.generate_mention(user.discord_ID) +
                               " mas na " + system + "(/dev/shm) " +
                               str(count) + " souboru semaforu")
                if avg_time > 9:
                    await ctx.send("Lezi ti tam prumerne uz " +
                                   str(avg_time) + " minut, ty prase")
                if login_not_in_name:
                    await ctx.send("Nemas v nazvu tvuj login takze muzes" +
                                    " mit kolize s ostatnima, ty prase")


    if parsed_processes != dict():
        for login, array in parsed_processes.copy().items():
            user = session.query(Permit).\
                filter(Permit.login == login).one_or_none()
            count = len(array)
            avg_time = sum(array) // count

            person = session.query(Valid_person).\
                filter(Valid_person.login == login).one_or_none()

            if "BIT" not in person.year and "FEKT" not in person.year:
                if login in parsed_processes:
                    parsed_processes.pop(login)
                continue

            if user is None:
                await ctx.send("Nejakeho " + login + " co neni na serveru")
            else:
                await ctx.send(utils.generate_mention(user.discord_ID) +
                               " mas na " + system + " " + str(count) +
                               " procesu, bezicich prumerne " +
                               str(avg_time) + " minut, ty prase")
    
    if (parsed_memory == dict() and parsed_semaphores == dict()
            and parsed_processes == dict() and parsed_files == dict()):
        await ctx.send("Na " + system + " uklizeno <:HYPERS:493154327318233088>")


class IOS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.cooldown(rate=5, per=30.0, type=commands.BucketType.user)
    @commands.has_any_role(461550034668748800, 591372495936815114,
                           461550323727859712)
    @commands.command()
    async def ios(self, ctx):
        process = subprocess.Popen(["ssh", "merlin"], stdout=subprocess.PIPE)
        output, error = process.communicate()
        memory, rest = output.decode('utf-8').split("semafory:\n")
        semaphores, processes = rest.split("procesy:\n")
        try:
            parsed_memory = parse_memory(memory)
            parsed_semaphores, parsed_files = parse_semaphores(semaphores)
            parsed_processes = parse_processes(processes)
        except IndexError:
            await ctx.send("Toastere mas bordel v parsovani")

        await print_output(ctx, "merlinovi", parsed_memory, parsed_semaphores,
                           parsed_files, parsed_processes)

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
        except IndexError:
            await ctx.send("Toastere mas bordel v parsovani")

        # eva doesn't seem to have /dev/shm
        await print_output(ctx, "eve", parsed_memory, parsed_semaphores, dict(), parsed_processes)
        await ctx.send("Pokud nevite jak po sobe uklidit checknete: " +
                       "https://discordapp.com/channels/" + 
                       "461541385204400138/534431057001316362/" +
                       "698701631495340033")

    @ios.error
    async def ios_role_checks_error(self, ctx, error):
        if isinstance(error, commands.errors.MissingAnyRole):
            await ctx.send('Na tohle maji prava jen Helper+. ' +
                           '<:KKomrade:484470873001164817>')


def setup(bot):
    bot.add_cog(IOS(bot))
