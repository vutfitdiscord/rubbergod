import argparse
import logging

import disnake
from disnake import AllowedMentions, Intents, TextChannel
from disnake.ext import commands

import database.db_migrations as migrations
from buttons.contestvote import ContestView
from buttons.poll import (PollBasicView, PollBooleanView, PollCloseView,
                          PollOpinionView, PollVotersView)
from buttons.report import (ReportAnonymView, ReportAnswerOnlyView,
                            ReportGeneralView, ReportMessageView)
from config.app_config import config
from config.messages import Messages
from features import presence
from features.error import ErrorLogger

logger = logging.getLogger('disnake')
logger.setLevel(logging.WARNING)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

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
    print("Init complete")
    exit(0)

is_initialized = False

intents = Intents.none()
intents.guilds = True
intents.members = True
intents.emojis = True
intents.messages = True
intents.message_content = True
intents.reactions = True
intents.presences = True
intents.moderation = True
intents.automod_execution = True

command_sync_flags = commands.CommandSyncFlags()
command_sync_flags.sync_commands_debug = False

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or(*config.command_prefix),
    help_command=None,
    case_insensitive=True,
    allowed_mentions=AllowedMentions(roles=False, everyone=False, users=True),
    intents=intents,
    command_sync_flags=command_sync_flags
)

presence = presence.Presence(bot)
err_logger = ErrorLogger(bot)


@bot.event
async def on_ready():
    """If RubberGod is ready"""
    # Inspired from https://github.com/sinus-x/rubbergoddess/blob/master/rubbergoddess.py
    global is_initialized
    if is_initialized:
        return
    is_initialized = True

    views = [
        ReportGeneralView(bot),
        ReportMessageView(bot),
        ReportAnonymView(bot),
        ReportAnswerOnlyView(bot),
        PollBasicView(bot),
        PollBooleanView(bot),
        PollOpinionView(bot),
        PollCloseView(bot),
        PollVotersView(bot),
        ContestView(bot)
    ]
    for view in views:
        bot.add_view(view)

    bot_room: TextChannel = bot.get_channel(config.bot_room)
    if bot_room is not None:
        await bot_room.send(Messages.on_ready_message)

    await presence.set_presence()
    print("Ready")


@bot.event
async def on_button_click(inter: disnake.MessageInteraction):
    if inter.component.custom_id in ["trash:delete", "bookmark:delete"]:
        try:
            await inter.message.delete()
        except disnake.NotFound:
            pass


@bot.event
async def on_error(event, *args, **kwargs):
    return await err_logger.handle_event_error(event, args)


# Create missing tables at start
migrations.init_db()

bot.load_extension("cogs.system")
print("System cog loaded")

for extension in config.extensions:
    bot.load_extension(f"cogs.{extension}")
    print(f"{extension} loaded")

bot.run(config.key)
