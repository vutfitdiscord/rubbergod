import traceback
import argparse

from discord.ext import commands

import utils
from config import config
from features import presence

import repository.db_migrations as migrations

parser = argparse.ArgumentParser()
parser.add_argument('--load_dump', type=str,
                    help='Imports SQL dump from SQL file to database.',
                    metavar='filepath.sql')
parser.add_argument('--load_subjects', action='store_true',
                    help='Fills DB with subjects.')
parser.add_argument('--init_db', action='store_true',
                    help='Creates missing DB tables without start bot.')
args = parser.parse_args()

if args.load_dump is not None:
    migrations.load_dump(args.load_dump)
    exit(0)
elif args.load_subjects:
    migrations.load_subjects()
    exit(0)
elif args.init_db:
    migrations.init_db()
    print('Init complete')
    exit(0)

config = config.Config

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or(*config.command_prefix),
    help_command=None,
    case_insensitive=True)

presence = presence.Presence(bot)


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
@commands.check(utils.is_bot_owner)
async def pull(ctx):
    try:
        utils.git_pull()
        await ctx.send("Git pulled")
    except Exception:
        await ctx.send("Git pull error")


@bot.command()
@commands.check(utils.is_bot_owner)
async def load(ctx, extension):
    try:
        bot.load_extension(f'cogs.{extension}')
        await ctx.send(f'{extension} loaded')
    except Exception as e:
        await ctx.send(f"loading error\n```\n{e}```")


@bot.command()
@commands.check(utils.is_bot_owner)
async def unload(ctx, extension):
    try:
        bot.unload_extension(f'cogs.{extension}')
        await ctx.send(f'{extension} unloaded')
    except Exception as e:
        await ctx.send(f"unloading error\n```\n{e}```")


@bot.command()
@commands.check(utils.is_bot_owner)
async def reload(ctx, extension):
    try:
        bot.reload_extension(f'cogs.{extension}')
        await ctx.send(f'{extension} reloaded')
    except Exception as e:
        await ctx.send(f"reloading error\n```\n{e}```")


@reload.error
@load.error
@unload.error
@pull.error
async def missing_arg_error(ctx, error):
    if isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send('Missing argument.')
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send(
            utils.fill_message("insufficient_rights", user=ctx.author.id))

# Create missing tables at start
migrations.init_db()

for extension in config.extensions:
    bot.load_extension(f'cogs.{extension}')
    print(f'{extension} loaded')

bot.run(config.key)
