from discord import Member
from discord.ext import commands
from config import config, messages
from repository.database import session
from repository.database.verification import Permit
import discord
import utils
import subprocess
import datetime


config = config.Config
Messages = messages.Messages


def running_for(time):
    now = datetime.datetime.now()
    hours = now.hour - int(time.split(':')[0])
    minutes = now.minute - int(time.split(':')[1])
    return hours * 60 + minutes

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
    semaphores, files = semaphores.split("soubory semaforu:\n")
    parsed = dict()
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

    parsed_files = dict()
    for line in files.strip().splitlines():
        line = line.split()
        login = line[2]
        if login[0] != 'x':
            continue
        last_change = " ".join(line[5:7])
        name = line[7]
        if "ADBE" in name:
            continue
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
        time = line[8]
        uptime = running_for(time)
        if uptime > 10:
            if login not in parsed:
                parsed[login] = list()
            parsed[login].append(uptime)
    return parsed


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
        if parsed_memory != dict():
            for login, array in parsed_memory.items():
                user = session.query(Permit).\
                    filter(Permit.login == login).one_or_none()
                count = len(array)
                avg_time = sum(array) // count

                if user is None:
                    await ctx.send("Sdilenou pamet nechava nejaky " + login +
                                   " co neni na serveru")
                else:
                    await ctx.send(utils.generate_mention(user.discord_ID) +
                                   " mas na merlinovi " + str(count) +
                                   " sdilene pameti, ztracene prumerne " +
                                   str(avg_time) + " minut, ty prase")

        if parsed_semaphores != dict():
            for login, array in parsed_semaphores.items():
                user = session.query(Permit).\
                    filter(Permit.login == login).one_or_none()
                count = len(array)
                avg_time = sum(array) // count

                if user is None:
                    await ctx.send("Semafory nechava nejaky " + login + " co neni na serveru")
                else:
                    await ctx.send(utils.generate_mention(user.discord_ID) +
                                   " mas na merlinovi " + str(count) +
                                   " semaforu, lezicich tam prumerne " +
                                   str(avg_time) + " minut, ty prase")

        if parsed_files != dict():
            for login, array in parsed_files.items():
                user = session.query(Permit).\
                    filter(Permit.login == login).one_or_none()
                login_not_in_name = array[1]
                array = array[0]
                count = len(array)
                avg_time = sum(array) // count

                if user is None:
                    await ctx.send("Soubory semaforu nechava nejaky " +
                                   login + " co neni na serveru")
                else:
                    await ctx.send(utils.generate_mention(user.discord_ID) +
                                   " mas na merlinovi(/dev/shm) " +
                                   str(count) + " souboru semaforu")
                    if avg_time > 9:
                        await ctx.send("Lezi ti tam prumerne uz " +
                                       str(avg_time) + " minut, ty prase")
                    if login_not_in_name:
                        await ctx.send("Nemas v nazvu tvuj login takze muzes" +
                                        " mit kolize s ostatnima, ty prase")


        if parsed_processes != dict():
            for login, array in parsed_processes.items():
                user = session.query(Permit).\
                    filter(Permit.login == login).one_or_none()
                count = len(array)
                avg_time = sum(array) // count

                if user is None:
                    await ctx.send("Nejakeho " + login + " co neni na serveru")
                else:
                    await ctx.send(utils.generate_mention(user.discord_ID) +
                                   " mas na merlinovi " + str(count) +
                                   " procesu, bezicich prumerne " +
                                   str(avg_time) + " minut, ty prase")
        
        if (parsed_memory == dict() and parsed_semaphores == dict()
                and parsed_processes == dict() and parsed_files == dict()):
            await ctx.send("Uklizeno <:HYPERS:493154327318233088>")
        else:
            await ctx.send("Pokud nevite jak po sobe uklidit checknete: " +
                           "https://discordapp.com/channels/" + 
                           "461541385204400138/534431057001316362/" +
                           "698701631495340033")


    @ios.error
    async def ios_role_checks_error(self, ctx, error):
        if isinstance(error, commands.errors.MissingAnyRole):
            await ctx.send('Nothing to see here comrade. ' +
                           '<:KKomrade:484470873001164817>')


def setup(bot):
    bot.add_cog(IOS(bot))
