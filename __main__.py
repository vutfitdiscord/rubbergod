import discord
from repository import rng, karma, user, utils, roll_dice
from config import config
import mysql.connector
import random
import string
import smtplib
import ssl
import traceback
import datetime


client = discord.Client()
config = config.Config()
utils = utils.Utils()
karma = karma.Karma()
rng = rng.Rng()
user = user.User()
roll_dice = roll_dice.Roll()
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


async def send_code(message):
    if len(str(message.content).split(" ")) != 2:
        await message.channel.send(
                "Očekávám 1 argument (login)\n")
        return

    if not user.has_role(message, config.verification_role):
        if str(message.content).split(" ")[1] == "xlogin00":
            guild = client.get_guild(config.guild_id)
            fp = await guild.fetch_emoji(585915845146968093)
            await message.channel.send("Tvuj login {} {}"
                                       .format(str(fp),
                                               utils.generate_mention(
                                                   message.author.id)))
            return

        db_record = user.find_login_to_mail(message)
        if db_record:
            # get server permit role

            code = ''.join(random.choices(string.ascii_uppercase +
                                          string.digits, k=20))

            login = str(message.content).split(" ")[1]
            email_message = "!verify " + login + " " + code
            password = config.email_pass
            port = 465
            context = ssl.create_default_context()
            sender_email = "toasterrubbergod@gmail.com"
            receiver_email = login + "@stud.fit.vutbr.cz"
            subject = "FIT Discord verifikace"
            mail_content = 'Subject: {}\n\n{}'.format(subject, email_message)

            with smtplib.SMTP_SSL("smtp.gmail.com", port,
                                  context=context) as server:
                server.login("toasterrubbergod@gmail.com", password)
                server.sendmail(sender_email, receiver_email, mail_content)

            user.save_mail(message, code)

            await message.channel.send(("Kód byl odeslán " +
                                        "na tvůj mail " +
                                        "(@stud.fit.vutbr.cz)! {}\n" +
                                        "Pro verifikaci použij:\n" +
                                        "!verify xlogin00 kód"
                                        ).format(utils.generate_mention(
                                                     message.author.id)))
        else:
            await message.channel.send(("Login nenalezen nebo jsi již " +
                                        "prošel tímhle krokem {} {}"
                                        ).format(utils.generate_mention(
                                                     message.author.id),
                                                 utils.generate_mention(
                                                     config.admin_id)))
    else:
        await message.channel.send("Už si byl verifikován {} {}"
                                   .format(utils.generate_mention(
                                               message.author.id),
                                           utils.generate_mention(
                                           config.admin_id)))
    try:
        await message.delete()
    except discord.errors.Forbidden:
        return


async def verify(message):
    """"Verify if VUT login is from database"""
    if len(str(message.content).split(" ")) != 3:
        await message.channel.send(
                "Očekávám 2 argumenty (login a kód)\n" +
                "Pro získaní kódu použij `!getcode xlogin00`")
        return

    if not user.has_role(message, config.verification_role):
        if str(message.content).split(" ")[1] == "xlogin00":
            guild = client.get_guild(config.guild_id)
            fp = await guild.fetch_emoji(585915845146968093)
            await message.channel.send("Tvůj login {} {}"
                                       .format(str(fp),
                                               utils.generate_mention(
                                                   message.author.id)))
            return
        if str(message.content).split(" ")[2] == "kód":
            guild = client.get_guild(config.guild_id)
            fp = await guild.fetch_emoji(585915845146968093)
            await message.channel.send("Kód který ti přišel na mail {} {}"
                                       .format(str(fp),
                                               utils.generate_mention(
                                                   message.author.id)))
            return

        db_record = user.find_login(message)
        if db_record:
            db_record = db_record[2].split()
            year = None
            if len(db_record) == 3:
                if db_record[0] == "FIT":
                    db_record[2] = int(db_record[2][:-1])
                    if db_record[1] == "BIT":
                        year = "BIT"
                        if db_record[2] < 4:
                            year = str(db_record[2]) + year
                        else:
                            year = "4BIT+"
                    elif db_record[1] in ["MBS", "MBI", "MIS", "MIN",
                                          "MMI", "MMM", "MGM", "MGMe",
                                          "MPV", "MSK"]:
                        year = "MIT"
                        if db_record[2] < 3:
                            year = str(db_record[2]) + year
                        else:
                            year = "3MIT+"
                    elif db_record[1] == "DVI4":
                        year = "PhD+"
                elif db_record[0] == "FEKT":
                    year = "FEKT"

            if year is None:
                await message.channel.send(
                    "Čauec {}, nechám {} aby to udělal manuálne\nYear:`{}`"
                    .format(utils.generate_mention(
                                message.author.id),
                            utils.generate_mention(
                                config.admin_id),
                            str(db_record)))
                return

            try:
                # get server permit role
                verify = discord.utils.get(message.guild.roles,
                                           name=config.verification_role)
                year = discord.utils.get(message.guild.roles, name=year)
                member = message.author
            except AttributeError:
                # jsme v PM
                guild = client.get_guild(config.guild_id)
                verify = discord.utils.get(guild.roles,
                                           name=config.verification_role)
                year = discord.utils.get(guild.roles, name=year)
                member = guild.get_member(message.author.id)

            await member.add_roles(verify)
            await member.add_roles(year)
            user.save_record(message)
            await message.channel.send("Gratuluji, byl si verifikován! {}"
                                       .format(utils.generate_mention(
                                                   message.author.id)))
        else:
            await message.channel.send(("Login nenalezen nebo jsi jiz " +
                                        "prosel timhle krokem {} {}"
                                        ).format(utils.generate_mention(
                                                     message.author.id),
                                                 utils.generate_mention(
                                                     config.admin_id)))
    else:
        await message.channel.send("Už si byl verifikován {} {}"
                                   .format(utils.generate_mention(
                                               message.author.id),
                                           utils.generate_mention(
                                               config.admin_id)))
    try:
        await message.delete()
    except discord.errors.Forbidden:
        return


async def pick(message):
    """"Pick an option"""
    option = rng.pick_option(message)
    if option:
        await message.channel.send("{} {}"
                                   .format(option,
                                           utils.generate_mention(
                                               message.author.id)))


async def karma_leaderboard(message, order):
    board = karma.get_leaderboard(order)
    i = 1
    if order == "DESC":
        output = "==================\n KARMA LEADERBOARD \n"
        output += "==================\n"
    else:
        output = "==================\n KARMA BAJKARBOARD \n"
        output += "==================\n"
    guild = client.get_guild(config.guild_id)
    for user in board:
        username = guild.get_member(int(user[0]))
        if username is None:
            continue
        username = str(username.name)
        line = '{} - {}:  {} pts\n'.format(i, username, user[1])
        output = output + line
        i = i + 1
    # '\n Full leaderboard - TO BE ADDED (SOON*tm*) \n'
    await message.channel.send(output)


async def show_karma(message):
    await message.channel.send(str(karma.get_karma(message.author.id)))


# Returns list of role names and emotes that represent them
async def get_join_role_data(message):
    input_string = message.content
    input_string = input_string.replace(" - ", " ")
    input_string = input_string.replace(": ", " ")
    input_string = input_string.replace("**", "")
    output = []
    try:
        input_string = (input_string[input_string.index('\n')+1:]
                        .strip().split('\n'))
    except ValueError:
        await message.channel.send("{} nesprávny formát. Použi !god"
                                   .format(utils.generate_mention(
                                        message.author.id)))
        return output
    for line in input_string:
        line = line.split()
        if len(line) > 1:
            line = [line[0], line[1]]
            output.append(line)
        else:
            await message.channel.send("{} {} je neplatný riadok"
                                       .format(utils.generate_mention(
                                            message.author.id), line[0]))
    return output


# Adds reactions to message
async def message_role_reactions(message, data):
    if message.channel.type is not discord.ChannelType.text:
        await message.channel.send("Nepises na serveru takze predpokladam "
                                   "ze myslis role VUT FIT serveru")
        guild = client.get_guild(config.guild_id)
    else:
        guild = message.guild
    for line in data:
        if (discord.utils.get(guild.roles,
                              name=line[0]) is None):
            await message.channel.send("{} {} nie je rola"
                                       .format(utils.generate_mention(
                                           message.author.id), line[0]))
        else:
            try:
                await message.add_reaction(line[1])
            except discord.errors.HTTPException:
                await message.channel.send("{} {} pre rolu {} nie je emote"
                                           .format(utils.generate_mention(
                                               message.author.id),
                                               line[1], line[0]))


# Adds a role for user based on reaction
async def add_role_on_reaction(role, member, message, guild):
    role = discord.utils.get(guild.roles,
                             name=role)
    max_role = discord.utils.get(guild.roles,
                                 name="Rubbergod")
    if role is not None:
        if role < max_role:
            await member.add_roles(role)
        else:
            await message.channel.send("{} na pridanie role {} nemáš práva"
                                       .format(utils.generate_mention(
                                          member.id), role.name))


# Removes a role for user based on reaction
async def remove_role_on_reaction(role, member, message, guild):
    role = discord.utils.get(guild.roles,
                             name=role)
    max_role = discord.utils.get(guild.roles,
                                 name="Rubbergod")
    if role is not None:
        if role in member.roles:
            if role < max_role:
                await member.remove_roles(role)
            else:
                await message.channel.send("{} na odobranie role {} "
                                           "nemáš práva"
                                           .format(utils.generate_mention(
                                              member.id), role.name))


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

    if message.content.startswith(config.command_prefix):
        separator_pos = message.content.find(' ')
        if separator_pos < 0:
            separator_pos = len(message.content) # args will be an empty string

        # strip prefix
        command = message.content[len(config.command_prefix):separator_pos]
        args = message.content[separator_pos+1:]

        await run_command(message, command, args)

    elif message.content.startswith(config.role_string):
        role_data = await get_join_role_data(message)
        await message_role_reactions(message, role_data)


async def run_command(message, command, args):

    if command == "verify":
        await verify(message)

    elif command == "getcode":
        await send_code(message)

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
                        await karma.revote(message, config)
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
                        await karma.vote(message, config)
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
            await show_karma(message)
            await botroom_check(message)

    # END KARMA COMMAND

    elif command == "leaderboard":
        await karma_leaderboard(message, 'DESC')
        await botroom_check(message)

    elif command == "bajkarboard":
        await karma_leaderboard(message, 'ASC')
        await botroom_check(message)

    elif command == "god":
        await message.channel.send(config.info())

    elif command == "diceroll":
        await message.channel.send(roll_dice.roll_dice(args, config))
        await botroom_check(message)


@client.event
async def on_raw_reaction_add(payload):
    channel = client.get_channel(payload.channel_id)
    if channel.type is discord.ChannelType.text:
        guild = channel.guild
    else:
        guild = client.get_guild(config.guild_id)
    member = guild.get_member(payload.user_id)
    message = await channel.fetch_message(payload.message_id)
    if member is not None:
        if payload.emoji.is_custom_emoji():
            emoji = client.get_emoji(payload.emoji.id)
        else:
            emoji = payload.emoji.name
        if not(member.bot):
            if message.content.startswith(config.role_string):
                role_data = await get_join_role_data(message)
                for line in role_data:
                    if str(emoji) == line[1]:
                        await add_role_on_reaction(line[0], member,
                                                   message, guild)
                        break
                else:
                    if emoji is None:
                        await message.remove_reaction(payload.emoji, member)
                    else:
                        await message.remove_reaction(emoji, member)
            elif message.content.startswith(config.vote_message):
                if emoji is None:
                    await message.remove_reaction(payload.emoji, member)
                elif emoji not in ["✅", "❌", "0⃣"]:
                    await message.remove_reaction(emoji, member)
            elif type(emoji) is not str and member.id != message.author.id:
                karma.karma_emoji(message.author, payload.emoji.id)


@client.event
async def on_raw_reaction_remove(payload):
    channel = client.get_channel(payload.channel_id)
    if channel.type is discord.ChannelType.text:
        guild = channel.guild
    else:
        guild = client.get_guild(config.guild_id)
    member = guild.get_member(payload.user_id)
    message = await channel.fetch_message(payload.message_id)
    if member is not None:
        if payload.emoji.is_custom_emoji():
            emoji = client.get_emoji(payload.emoji.id)
        else:
            emoji = payload.emoji.name
        if message.content.startswith(config.role_string):
            role_data = await get_join_role_data(message)
            for line in role_data:
                if str(emoji) == line[1]:
                    await remove_role_on_reaction(line[0], member,
                                                  message, guild)
                    break
        elif type(emoji) is not str and member.id != message.author.id:
            karma.karma_emoji_remove(message.author, payload.emoji.id)


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
