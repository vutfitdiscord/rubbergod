import traceback
import argparse
import logging

from disnake import Embed, TextChannel, AllowedMentions, Intents
from disnake.ext import commands

import utils
from config.messages import Messages
from config.app_config import config
from features import presence

import repository.db_migrations as migrations

logger = logging.getLogger('discord')
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
intents.reactions = True
intents.presences = True

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or(*config.command_prefix),
    help_command=None,
    case_insensitive=True,
    allowed_mentions=AllowedMentions(roles=False, everyone=False, users=True),
    intents=intents,
)

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
    channel_out = bot.get_channel(config.bot_dev_channel)
    output = traceback.format_exc()
    print(output)

    embeds = []
    guild = None
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
            message_id = arg.message_id
            if hasattr(arg, 'guild_id'):
                guild = bot.get_guild(arg.guild_id)
                event_guild = guild.name
                channel = guild.get_channel(arg.channel_id)
                message = await channel.fetch_message(arg.message_id)
                message = message.content[:1000]
            else:
                event_guild = "DM"
                message = arg.message_id

            user = bot.get_user(arg.user_id)
            if not user:
                user = arg.user_id
            else:
                channel = bot.get_channel(arg.channel_id)
                if channel:
                    message = await channel.fetch_message(arg.message_id)
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
                    message = arg.message_id
                user = str(user)

        embed = Embed(title=f"Ignoring exception in event '{event}'", color=0xFF0000)
        embed.add_field(name="Zpráva", value=message, inline=False)
        if not guild or guild.id != config.guild_id:
            embed.add_field(name="Guild", value=event_guild)

        if event != "on_message":
            if arg.member:
                reaction_from = str(arg.member)
            else:
                reaction_from = user
            embed.add_field(name="Reakce od", value=reaction_from)
            embed.add_field(name="Reaction", value=arg.emoji)
            embed.add_field(name="Typ", value=arg.event_type)
        if guild:
            link = f"https://discord.com/channels/{guild.id}/{channel.id}/{message_id}"
            embed.add_field(name="Link", value=link, inline=False)
        embeds.append(embed)

    if channel_out is not None:
        output = utils.cut_string(output, 1900)
        for embed in embeds:
            await channel_out.send(embed=embed)
        for message in output:
            await channel_out.send(f"```\n{message}```")


# Create missing tables at start
migrations.init_db()

bot.load_extension("cogs.system")
print("System cog loaded")

for extension in config.extensions:
    bot.load_extension(f"cogs.{extension}")
    print(f"{extension} loaded")

bot.run(config.key)
