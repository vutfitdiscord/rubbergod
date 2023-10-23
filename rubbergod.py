import argparse
import logging
import sys
import traceback

import disnake
import sqlalchemy
from disnake import AllowedMentions, Embed, HTTPException, Intents, TextChannel
from disnake.errors import DiscordServerError
from disnake.ext import commands

import database.db_migrations as migrations
from buttons.report import (ReportAnonymView, ReportAnswerOnlyView,
                            ReportGeneralView, ReportMessageView)
from config.app_config import config
from config.messages import Messages
from database import session
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
err_logger = ErrorLogger()


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
        ReportAnswerOnlyView(bot)
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
        await inter.message.delete()


@bot.event
async def on_error(event, *args, **kwargs):
    e = sys.exc_info()[1]
    if isinstance(e, DiscordServerError) and e.status == 503:
        return

    if isinstance(e, sqlalchemy.exc.InternalError):
        session.rollback()
        return

    if isinstance(e, HTTPException):
        # 50007: Cannot send messages to this user
        if e.code == 50007:
            return

    channel_out = bot.get_channel(config.bot_dev_channel)
    output = traceback.format_exc()
    print(output)

    embeds = []
    guild = None
    user = bot.user
    for arg in args:
        if event == "on_message":
            message = arg.content
            message_id = arg.id
            channel = arg.channel
            user = arg.author
            if hasattr(arg, 'guild') and arg.guild:
                event_guild = arg.guild.name
                guild = arg.guild
            else:
                event_guild = "DM"

        else:  # on_raw_reaction_add/remove
            message_id = getattr(arg, 'message_id', None)
            channel_id = getattr(arg, 'channel_id', None)
            user_id = getattr(arg, 'user_id', None)
            if hasattr(arg, 'guild_id'):
                guild = bot.get_guild(arg.guild_id)
                event_guild = guild.name
                if channel_id:
                    channel = guild.get_channel(channel_id)
                    if message_id and channel:
                        message = await channel.fetch_message(message_id)
                        if message is not None:
                            message = message.content[:1000]
            else:
                event_guild = "DM"
                message = message_id

            if user_id:
                user = bot.get_user(arg.user_id)
            if not user:
                user = arg.user_id
            else:
                if channel_id:
                    channel = bot.get_channel(channel_id)
                    if channel and message_id:
                        message = await channel.fetch_message(message_id)
                        if message:
                            if message.content:
                                message = message.content[:1000]
                            elif message.embeds:
                                embeds.extend(message.embeds)
                                message = "Embed v předchozí zprávě"
                            elif message.attachments:
                                message_out = ""
                                for attachment in message.attachments:
                                    message_out += f"{attachment.url}\n"
                                message = message_out
                    else:
                        message = message_id

        count = err_logger.log_error_date()
        embed = Embed(
            title=f"{count} days without an accident.\nIgnoring exception in event '{event}'",
            color=0xFF0000,
        )
        embed.add_field(name="Zpráva", value=message, inline=False)
        if not guild or guild.id != config.guild_id:
            embed.add_field(name="Guild", value=event_guild)

        if event != "on_message":
            if hasattr(arg, 'member'):
                reaction_from = str(arg.member)
            else:
                reaction_from = user
            embed.add_field(name="Reakce od", value=reaction_from)
            embed.add_field(name="Reaction", value=getattr(arg, 'emoji', None))
            embed.add_field(name="Typ", value=getattr(arg, 'event_type', None))
        if guild:
            link = f"https://discord.com/channels/{guild.id}/{channel.id}/{message_id}"
            embed.add_field(name="Link", value=link, inline=False)
        err_logger.set_image(embed, user, count)
        embeds.append(embed)

    if channel_out is not None:
        for embed in embeds:
            await channel_out.send(embed=embed)
        await err_logger.send_output(output, channel_out)


# Create missing tables at start
migrations.init_db()

bot.load_extension("cogs.system")
print("System cog loaded")

for extension in config.extensions:
    bot.load_extension(f"cogs.{extension}")
    print(f"{extension} loaded")

bot.run(config.key)
