import discord
from repository import rng, karma, user, utils
from config import config
import mysql.connector


client = discord.Client()
config = config.Config()
utils = utils.Utils()
karma = karma.Karma()
rng = rng.Rng()
user = user.User()


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
        cursor.execute('UPDATE bot_karma SET nick="{}", '
                       'avatar_url="{}" WHERE member_id="{}"'
                       .format(username,
                               user.avatar_url.replace(".webp", ".png"),
                               item[0]))
        print("{} - {}".format(username,
                               user.avatar_url.replace(".webp", ".png")))
    db.commit()
    db.close()


async def verify(message):
    """"Verify if VUT login is from database"""
    if len(str(message.content).split(" ")) != 3:
        await message.channel.send(
                "Debile musis to volat s 2ma argumentama " +
                "ale to ti matthew nerekne")
        return

    if not user.has_role(message, config.verification_role):
        db_record = user.find_login(message)
        if db_record:
            # get server permit role
            verify = discord.utils.get(message.guild.roles,
                                       name=config.verification_role)

            print(db_record)
            if db_record[3] == "FIT BIT 1r":
                year = discord.utils.get(message.guild.roles,
                                         "bit1")
            elif db_record[3] == "FIT BIT 2r":
                year = discord.utils.get(message.guild.roles,
                                         "bit2")
            else:
                await message.channel.send(
                    "Hey {}, I'll let {} handle this manualy\nYear:`{}`"
                    .format(utils.generate_mention(
                                message.author.id),
                            utils.generate_mention(
                                config.admin_id),
                            db_record[3]))
                return

            user.save_record(message)
            await client.add_roles(message.author, verify)
            await client.add_roles(message.author, year)
            await message.channel.send("Congrats, you have been verified! {}"
                                       .format(utils.generate_mention(
                                                   message.author.id)))
        else:
            await message.channel.send("Not found {} {}"
                                       .format(utils.generate_mention(
                                                   message.author.id),
                                               utils.generate_mention(
                                                   config.admin_id)))
    else:
        await message.channel.send("You have already been verified {} {}"
                                   .format(utils.generate_mention(
                                               message.author.id),
                                           utils.generate_mention(
                                               config.admin_id)))
    await message.delete()


async def pick(message):
    """"Pick an option"""
    option = rng.pick_option(message)
    if option:
        await message.channel.send("{} {}"
                                   .format(option,
                                           utils.generate_mention(
                                               message.author.id)))


async def karma_leaderboard(message):
    board = karma.get_leaderboard()
    i = 1
    output = "==================\n KARMA LEADERBOARD \n==================\n"
    for user in board:
        username = await client.get_user_info(user[0])
        username = str(username).split('#')[0]
        line = '{} - {} - {} pts\n'.format(i, username, user[1])
        output = output + line
        i = i + 1
    output = output + '\n Full leaderboard - http://bit.ly/godboard \n'
    await message.channel.send(output)


async def show_karma(message):
    await message.channel.send(str(karma.get_karma(message.author.id)))


#                                      #
#              COMMANDS                #
#                                      #

@client.event
async def on_message(message):

    if message.author == client.user:
        return

    elif message.content.startswith("!verify"):
        await verify(message)

    elif message.content.startswith("!roll"):
        await message.channel.send(rng.generate_number(message))

    elif message.content.startswith("!flip"):
        await message.channel.send(rng.flip())

    elif message.content.startswith("!week"):
        await message.channel.send(rng.week())

    elif message.content.startswith("!pick"):
        await pick(message)

    elif message.content.startswith("!karma"):
        await show_karma(message)

    elif message.content.startswith("!leaderboard"):
        await karma_leaderboard(message)

    elif message.content.startswith("!god"):
        await message.channel.send(config.info())


@client.event
async def on_reaction_add(reaction, user):
    if type(reaction.emoji) is not str:
        karma.karma_emoji(reaction.message.author, reaction.emoji.id)


@client.event
async def on_reaction_remove(reaction, user):
    if type(reaction.emoji) is not str:
        karma.karma_emoji_remove(reaction.message.author, reaction.emoji.id)


client.run(config.key)
