import discord
from repository import (rng, karma, user, utils, roll_dice,
                        reaction, verification)
from config import config
import mysql.connector
import traceback
import datetime


client = discord.Client()
config = config.Config()
utils = utils.Utils()
rng = rng.Rng()
user = user.User()
roll_dice = roll_dice.Roll()
karma = karma.Karma(client, utils)
reaction = reaction.Reaction(client, utils, karma)
verification = verification.Verification(client, utils, user)
arcas_time = datetime.datetime.utcnow() - datetime.timedelta(hours=1)


@client.event
async def on_ready():
    """If RGod is ready"""
    print("Ready")


async def update_web():
    db = mysql.connector.connect(**config.connection)
    cursor = db.cursor()
    cursor.execute('SELECT * FROM bot_karma')
    karma = cursor.fetchall()
    for item in karma:
        user = await client.get_user_info(item[0])
        client.get_user_info(item[0])
        username = str(user.name).split('#')[0]
        cursor.execute('UPDATE bot_karma SET nick=%s, '
                       'avatar_url=%s WHERE member_id=%s',
                       (username,
                        user.avatar_url.replace(".webp", ".png"),
                        item[0]))
        print("{} - {}".format(username,
                               user.avatar_url.replace(".webp", ".png")))
    db.commit()
    db.close()


async def botroom_check(message):
    room = await get_room(message)
    if room != "bot-room" and room is not None:
        await message.channel.send(
                "{} <:sadcat:576171980118687754> 👉 "
                "<#461549842896781312>\n"
                .format(utils.generate_mention(message.author.id)))


async def get_room(message):
    guild = client.get_guild(config.guild_id)
    try:
        if message.channel.guild == guild:
            return message.channel.name
    except AttributeError:
        # Jsme v PM
        return None


async def guild_check(message):
    try:
        guild = client.get_guild(config.guild_id)
        return message.channel.guild == guild
    except AttributeError:
        return False


async def pick(message):
    """"Pick an option"""
    option = rng.pick_option(message)
    if option:
        await message.channel.send("{} {}"
                                   .format(option,
                                           utils.generate_mention(
                                               message.author.id)))


#                                      #
#              COMMANDS                #
#                                      #

@client.event
async def on_error(event, *args, **kwargs):
    error = traceback.format_exc()
    channel = client.get_channel(config.log_channel_id)
    print(str(error))
    if channel is not None:
        await channel.send("```\n" + str(error) + "\n```")


@client.event
async def on_message(message):

    if message.author == client.user:
        return

    if user.has_role(message, config.bot_role):
        return

    if message.content.startswith(config.command_prefix):
        separator_pos = message.content.find(' ')
        if separator_pos < 0:
            # args will be an empty string
            separator_pos = len(message.content)

        # strip prefix
        command = message.content[len(config.command_prefix):separator_pos]
        args = message.content[separator_pos+1:]

        await run_command(message, command, args)

    elif message.content.startswith(config.role_string):
        role_data = await reaction.get_join_role_data(message)
        await reaction.message_role_reactions(message, role_data)


async def run_command(message, command, args):

    if command == "verify":
        await verification.verify(message)

    elif command == "getcode":
        await verification.send_code(message)

    elif command == "roll":
        await message.channel.send(rng.generate_number(message))
        await botroom_check(message)

    elif command == "flip" or command == "flippz":
        await message.channel.send(rng.flip())
        await botroom_check(message)

    elif command == "week":
        await message.channel.send(rng.week())

    elif command == "pick":
        await pick(message)
        await botroom_check(message)

    elif command == "karma":
        if args.startswith("get"):
            if not await guild_check(message):
                await message.channel.send(
                        "{}".format(config.server_warning))
            else:
                try:
                    await karma.get(message)
                    await botroom_check(message)
                except discord.errors.Forbidden:
                    return

        elif args.startswith("revote"):
            if not await guild_check(message):
                await message.channel.send(
                        "{}".format(config.server_warning))
            else:
                if message.channel.id == config.vote_room:
                    try:
                        await message.delete()
                        await karma.revote(message)
                    except discord.errors.Forbidden:
                        return
                else:
                    await message.channel.send(
                            "Tohle funguje jen v {}"
                            .format(discord.utils.get(message.guild.channels,
                                    id=config.vote_room)))

        elif args.startswith("vote"):
            if not await guild_check(message):
                await message.channel.send(
                        "{}".format(config.server_warning))
            else:
                if message.channel.id == config.vote_room:
                    try:
                        await message.delete()
                        await karma.vote(message)
                    except discord.errors.Forbidden:
                        return
                else:
                    await message.channel.send(
                            "Tohle funguje jen v {}"
                            .format(discord.utils.get(message.guild.channels,
                                    id=config.vote_room)))

        elif args.startswith("give"):
            if message.author.id == config.admin_id:
                await karma.karma_give(message)
            else:
                await message.channel.send(
                    "{} na použitie tohto príkazu nemáš práva"
                    .format(utils.generate_mention(message.author.id)))

        else:
            await message.channel.send(
                    str(karma.get_karma(message.author.id)))
            await botroom_check(message)

    # END KARMA COMMAND

    elif command == "leaderboard":
        await karma.leaderboard(message.channel, 'DESC')
        await botroom_check(message)

    elif command == "bajkarboard":
        await karma.leaderboard(message.channel, 'ASC')
        await botroom_check(message)

    elif command == "god":
        await message.channel.send(config.info)

    elif command == "diceroll":
        await message.channel.send(roll_dice.roll_dice(args))
        await botroom_check(message)


@client.event
async def on_raw_reaction_add(payload):
    await reaction.add(payload)


@client.event
async def on_raw_reaction_remove(payload):
    await reaction.remove(payload)


@client.event
async def on_typing(channel, user, when):
    global arcas_time
    if arcas_time + datetime.timedelta(hours=1) < when and\
            config.arcas_id == user.id:
        arcas_time = when
        gif = discord.Embed()
        gif.set_image(url="https://i.imgur.com/v2ueHcl.gif")
        await channel.send(embed=gif)


client.run(config.key)
