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
        cursor.execute('UPDATE bot_karma SET nick="{}", avatar_url="{}" WHERE member_id="{}"'.format(username, user.avatar_url.replace(".webp", ".png"), item[0]))
        print("{} - {}".format(username, user.avatar_url.replace(".webp", ".png")))
    db.commit()
    db.close()


async def permit(message):
    """"Verify if VUT login is from database"""
    if not user.has_role(message, config.verification_role):
        if user.find_login(message):
            role = discord.utils.get(message.server.roles, name=config.verification_role)  # get server permit role
            user.save_record(message)
            await client.add_roles(message.author, role)
            await client.send_message(message.channel, "Congrats, you have been verified! {}".format(utils.generate_mention(message.author.id)))
        else:
            await client.send_message(message.channel, "Not found {} {}".format(utils.generate_mention(message.author.id), utils.generate_mention(config.admin_id)))
    else:
        await client.send_message(message.channel, "You have already been verified {} {}".format(utils.generate_mention(message.author.id), utils.generate_mention(config.admin_id)))
    await client.delete_message(message)


async def pick(message):
    """"Pick an option"""
    option = rng.pick_option(message)
    if option:
        await client.send_message(message.channel, "{} {}".format(option, utils.generate_mention(message.author.id)))


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
    await client.send_message(message.channel, output)


async def show_karma(message):
    await client.send_message(message.channel, str(karma.get_karma(message.author.id)))


#                                      #
#              COMMANDS                #
#                                      #

@client.event
async def on_message(message):

    if message.author == client.user:
        return

    elif message.content.startswith("!permit"):
        await permit(message)

    elif message.content.startswith("!roll"):
        await client.send_message(message.channel, rng.generate_number(message))

    elif message.content.startswith("!flip"):
        await client.send_message(message.channel, rng.flip())

    elif message.content.startswith("!week"):
        await client.send_message(message.channel, rng.week())

    elif message.content.startswith("!pick"):
        await pick(message)

    elif message.content.startswith("!karma"):
        await show_karma(message)

    elif message.content.startswith("!leaderboard"):
        await karma_leaderboard(message)

    elif message.content.startswith("!god"):
        await client.send_message(message.channel, config.info())


@client.event
async def on_reaction_add(reaction, user):
    if type(reaction.emoji) is not str:
        karma.karma_emoji(reaction.message.author, reaction.emoji.id)


@client.event
async def on_reaction_remove(reaction, user):
    if type(reaction.emoji) is not str:
        karma.karma_emoji_remove(reaction.message.author, reaction.emoji.id)


client.run(config.key)
