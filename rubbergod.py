import traceback
import argparse

from discord import Embed
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
    print("Init complete")
    exit(0)

config = Config
is_initialized = False

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or(*config.command_prefix),
    help_command=None,
    case_insensitive=True,
    allowed_mentions=discord.AllowedMentions(roles=False, everyone=False, users=True),
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
        if arg.guild_id:
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
                else:
                    embeds.extend(message.embeds)
                    message = "Embed v předchozí zprávě"
            else:
                message = arg.message_id
            user = str(user)
        embed = Embed(title=f"Ignoring exception in event '{event}'", color=0xFF0000)
        embed.add_field(name="Zpráva", value=message, inline=False)
        if arg.guild_id != config.guild_id:
            embed.add_field(name="Guild", value=event_guild)

        if arg.member:
            reaction_from = str(arg.member)
        else:
            reaction_from = user
        embed.add_field(name="Reakce od", value=reaction_from)
        embed.add_field(name="Reaction", value=arg.emoji)
        embed.add_field(name="Typ", value=arg.event_type)
        if arg.guild_id:
            link = f"https://discord.com/channels/{arg.guild_id}/{arg.channel_id}/{arg.message_id}"
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
