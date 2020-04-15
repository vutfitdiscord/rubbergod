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

def unchanged_for(date):
    now = datetime.datetime.now()
    date = datetime.datetime.strptime(date, '%b %d %H:%M:%S')
    return (now - date.replace(year=now.year)).seconds // 60

def parse_memory(memory):
    parsed = dict()
    for line in memory.splitlines():
        line = line.split()
        login = line[1]
        if login[0] != 'x':
            continue
        last_change = " ".join(line[-3:])
        since_last_change = unchanged_for(last_change)
        if since_last_change > 10:
            if login not in parsed:
                parsed[login] = list()
            parsed[login].append(since_last_change)
    return parsed

def parse_semaphores(semaphores):
    parsed = dict()
    for line in semaphores.splitlines():
        line = line.split()
        login = line[1]
        if login[0] != 'x':
            continue
        last_change = " ".join(line[-4:-1])
        since_last_change = unchanged_for(last_change)
        if since_last_change > 10:
            if login not in parsed:
                parsed[login] = list()
            parsed[login].append(since_last_change)
    return parsed

def parse_processes(processes):
    parsed = dict()
    for line in processes.splitlines():
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
        parsed_memory = parse_memory(memory)
        parsed_semaphores = parse_semaphores(semaphores)
        parsed_processes = parse_processes(processes)
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
                and parsed_processes == dict()):
            await ctx.send("Uklizeno <:HYPERS:493154327318233088>")


    @ios.error
    async def ios_role_checks_error(self, ctx, error):
        if isinstance(error, commands.errors.MissingAnyRole):
            await ctx.send('Nothing to see here comrade. ' +
                           '<:KKomrade:484470873001164817>')


def setup(bot):
    bot.add_cog(IOS(bot))
