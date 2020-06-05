import re
import traceback

from discord.ext import commands

import utils
from config import config
from features import presence
from repository.database import database, session
from repository.database.karma import Karma, Karma_emoji
from repository.database.review import Review, ReviewRelevance, Subject
from repository.database.verification import Permit, Valid_person
from repository.database.image import Image
from repository.review_repo import ReviewRepository


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

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or(*config.command_prefix),
                   help_command=None,
                   case_insensitive=True)

presence = presence.Presence(bot)


def load_subjects():
    """
    Fills DB with subject shorcut from config file.
    This is needed for reviews feature.
    Run this just when you want to create DB fo reviews.
    """
    review_repo = ReviewRepository()
    for subject in config.subjects:
        review_repo.add_subject(subject)


@bot.event
async def on_ready():
    """If RGod is ready"""
    print("Ready")

    await presence.set_presence()


@bot.event
async def on_error(event, *args, **kwargs):
    channel = bot.get_channel(config.bot_dev_channel)
    output = traceback.format_exc()
    print(output)
    output = list(output[0+i:1900+i] for i in range(0, len(output), 1900))
    if channel is not None:
        for message in output:
            await channel.send("```\n{}```".format(message))


@bot.command()
async def pull(ctx):
    if ctx.author.id == config.admin_id:
        try:
            utils.git_pull()
            await ctx.send("Git pulled")
        except Exception:
            await ctx.send("Git pull error")
    else:
        await ctx.send(utils.fill_message("insufficient_rights", user=ctx.author.id))


@bot.command()
async def load(ctx, extension):
    if ctx.author.id == config.admin_id:
        try:
            bot.load_extension(f'cogs.{extension}')
            await ctx.send(f'{extension} loaded')
        except Exception:
            await ctx.send("loading error")
    else:
        await ctx.send(utils.fill_message("insufficient_rights", user=ctx.author.id))


@bot.command()
async def unload(ctx, extension):
    if ctx.author.id == config.admin_id:
        try:
            bot.unload_extension(f'cogs.{extension}')
            await ctx.send(f'{extension} unloaded')
        except Exception:
            await ctx.send("unloading error")
    else:
        await ctx.send(utils.fill_message("insufficient_rights", user=ctx.author.id))


@bot.command()
async def reload(ctx, extension):
    if ctx.author.id == config.admin_id:
        try:
            bot.reload_extension(f'cogs.{extension}')
            await ctx.send(f'{extension} reloaded')
        except Exception:
            await ctx.send("reloading error")
    else:
        await ctx.send(utils.fill_message("insufficient_rights", user=ctx.author.id))


@reload.error
@load.error
@unload.error
async def missing_arg_error(ctx, error):
    if isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send('Missing argument.')

database.base.metadata.create_all(database.db)
session.commit()  # Making sure

# load_subjects()

for extension in config.extensions:
    bot.load_extension(f'cogs.{extension}')
    print(f'{extension} loaded')

bot.run(config.key)
