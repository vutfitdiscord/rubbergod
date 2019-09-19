import re

from discord.ext import commands

import utils
from config import config, messages

from features import presence
from repository.database import database, session
from repository.database.karma import Karma, Karma_emoji
from repository.database.verification import Permit, Valid_person


# TODO move this ANYWHERE else
def load_dump():
    database.base.metadata.create_all(database.db)

    session.query(Karma).delete()
    session.query(Karma_emoji).delete()
    session.query(Permit).delete()
    session.query(Valid_person).delete()
    session.commit()

    data = database.base.metadata.tables.keys()
    for row in data:
        print(row)

    with open("backup-2019-08-17.sql", "r") as backup_file:
        data = backup_file.readlines()

    inserts = [line for line in data if line.startswith("INSERT")]

    karma_values = []
    for insert in inserts:
        values = insert.split("VALUES", 1)[1]
        if insert.startswith("INSERT INTO `bot_karma`"):
            values = values[1:-2].replace('\'', '')
            values = values.replace('(', '').replace(')', '')
            values = values.split(',')
            for i in range(0, len(values), 3):
                karma_values.append(Karma(member_ID=values[i],
                                          karma=values[i + 1]))
        elif insert.startswith("INSERT INTO `bot_karma_giving`"):
            values = values[1:-2].replace('\'', '')
            values = values.replace('(', '').replace(')', '')
            values = values.split(',')
            for i in range(0, len(values), 4):
                karma_values.append(Karma(member_ID=values[i],
                                          positive=values[i + 1],
                                          negative=values[i + 2]))
        elif insert.startswith("INSERT INTO `bot_karma_emoji`"):
            values = values[1:-2].replace('\'', '')
            values = values.replace('(', '').replace(')', '')
            values = values.split(',')
            for i in range(0, len(values), 2):
                session.add(Karma_emoji(emoji_ID=values[i],
                                        value=values[i + 1]))
        elif insert.startswith("INSERT INTO `bot_permit`"):
            values = values[1:-2]
            values = values.replace('(', '').replace(')', '')
            values = re.split(r',(?=\')', values)
            values = [value.replace('\'', '') for value in values]
            for i in range(0, len(values), 3):
                session.add(Permit(login=values[i],
                                   discord_ID=values[i + 2]))
        elif insert.startswith("INSERT INTO `bot_valid_persons`"):
            values = values[1:-2].replace('\'', '')
            values = values.replace('(', '').replace(')', '')
            values = values.split(',')
            for i in range(0, len(values), 5):
                session.add(Valid_person(login=values[i],
                                         name=values[i + 1],
                                         year=values[i + 2],
                                         code=values[i + 3]
                                         if values[i + 3] != "NULL" else None,
                                         status=values[i + 4]))

    for karma in karma_values:
        session.merge(karma)

    session.commit()


config = config.Config
messages = messages.Messages

bot = commands.Bot(command_prefix=commands.when_mentioned_or(
                                      *config.command_prefix),
                   help_command=None,
                   case_insensitive=True)

presence = presence.Presence(bot)

@bot.event
async def on_ready():
    """If RGod is ready"""
    print("Ready")

    await presence.set_presence()




@bot.command()
async def pull(ctx):
    if ctx.author.id == config.admin_id:
        try:
            utils.git_pull()
            await ctx.send("Git pulled")
        except:
            await ctx.send("Git pull error")
    else:
        await ctx.send(
            messages.insufficient_rights
            .format(user=utils.generate_mention(ctx.author.id)))


@bot.command()
async def load(ctx, extension):
    if ctx.author.id == config.admin_id:
        try:
            bot.load_extension(f'cogs.{extension}')
            await ctx.send(f'{extension} loaded')
        except:
            await ctx.send("loading error")
    else:
        await ctx.send(
            messages.insufficient_rights
            .format(user=utils.generate_mention(ctx.author.id)))


@bot.command()
async def unload(ctx, extension):
    if ctx.author.id == config.admin_id:
        try:
            bot.unload_extension(f'cogs.{extension}')
            await ctx.send(f'{extension} unloaded')
        except:
            await ctx.send("unloading error")
    else:
        await ctx.send(
            messages.insufficient_rights
            .format(user=utils.generate_mention(ctx.author.id)))


@bot.command()
async def reload(ctx, extension):
    if ctx.author.id == config.admin_id:
        try:
            bot.reload_extension(f'cogs.{extension}')
            await ctx.send(f'{extension} reloaded')
        except:
            await ctx.send("reloading error")
    else:
        await ctx.send(
            messages.insufficient_rights
            .format(user=utils.generate_mention(ctx.author.id)))


for extension in config.extensions:
    bot.load_extension(f'cogs.{extension}')
    print(f'{extension} loaded')

bot.run(config.key)
