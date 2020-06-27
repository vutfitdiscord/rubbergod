import traceback
import argparse

from discord import TextChannel
from discord.ext import commands

import utils
from config.messages import Messages
from config.app_config import Config
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

config = Config
is_initialized = False

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or(*config.command_prefix),
    help_command=None,
    case_insensitive=True)

presence = presence.Presence(bot)


@bot.event
async def on_ready():
    """If RubberGod is ready"""
    # Inspirated from https://github.com/sinus-x/rubbergoddess/blob/master/rubbergoddess.py
    global is_initialized
    if is_initialized:
        return
    is_initialized = True

    bot_room: TextChannel = bot.get_channel(config.bot_room)
    if bot_room is not None:
        await bot_room.send(Messages.on_ready_message)

    await presence.set_presence()
    print("Ready")


@bot.event
async def on_error(event, *args, **kwargs):
    channel = bot.get_channel(config.bot_dev_channel)
    output = traceback.format_exc()
    print(output)
    output = list(output[0+i:1900+i] for i in range(0, len(output), 1900))
    if channel is not None:
        for message in output:
            await channel.send("```\n{}```".format(message))


# Create missing tables at start
migrations.init_db()

bot.load_extension('cogs.system')
print('System cog loaded')

for extension in config.extensions:
    bot.load_extension(f'cogs.{extension}')
    print(f'{extension} loaded')

bot.run(config.key)
