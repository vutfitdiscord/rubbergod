import datetime
import traceback

import discord
from discord.ext import commands

import utils
from config import config, messages
from features import (karma, presence, verification, reaction)
from logic import roll_dice, rng
from repository import (karma_repo, user_repo)

config = config.Config
messages = messages.Messages

bot = commands.Bot(command_prefix=config.command_prefix,
                   help_command=None,
                   case_insensitive=True)

# Repositories (data access layer)
user_r = user_repo.UserRepository()
karma_r = karma_repo.KarmaRepository()

# Logic (functionality used by features or rubbergod directly)
roll_dice = roll_dice.Roll()
rng = rng.Rng()

# Features (layer talking to Discord)
verification = verification.Verification(bot, user_r)
karma = karma.Karma(bot, karma_r)
presence = presence.Presence(bot)
reaction = reaction.Reaction(bot, karma_r)

arcas_time = datetime.datetime.utcnow() - datetime.timedelta(hours=1)


async def botroom_check(message):
    room = await get_room(message)
    if room is not None and room.id != config.bot_room:
        await message.channel.send(
            "{} <:sadcat:576171980118687754> 👉 "
            "<#{}>\n"
            .format(utils.generate_mention(message.author.id),
                    config.bot_room))


async def get_room(message):
    guild = bot.get_guild(config.guild_id)
    try:
        if message.channel.guild == guild:
            return message.channel
    except AttributeError:
        # Jsme v PM
        return None


async def guild_check(message):
    try:
        guild = bot.get_guild(config.guild_id)
        return message.channel.guild == guild
    except AttributeError:
        return False


#                                    #
#              EVENTS                #
#                                    #


@bot.event
async def on_ready():
    """If RGod is ready"""
    print("Ready")

    await presence.set_presence()


@bot.event
async def on_message(message):
    if message.content.startswith(config.role_string):
        role_data = await reaction.get_join_role_data(message)
        await reaction.message_role_reactions(message, role_data)
    else:
        await bot.process_commands(message)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(messages.no_such_command)
    else:
        output = 'Ignoring exception in command {}:\n'.format(ctx.command)
        output += ''.join(traceback.format_exception(type(error),
                                                     error,
                                                     error.__traceback__))
        channel = bot.get_channel(config.log_channel_id)
        print(output)
        if channel is not None:
            await channel.send("```\n" + output + "\n```")


@bot.event
async def on_raw_reaction_add(payload):
    await reaction.add(payload)


@bot.event
async def on_raw_reaction_remove(payload):
    await reaction.remove(payload)


@bot.event
async def on_typing(channel, user, when):
    global arcas_time
    if arcas_time + datetime.timedelta(hours=1) < when and \
            config.arcas_id == user.id:
        arcas_time = when
        gif = discord.Embed()
        gif.set_image(url="https://i.imgur.com/v2ueHcl.gif")
        await channel.send(embed=gif)


#                                      #
#              COMMANDS                #
#                                      #


@bot.command()
async def verify(ctx):
    await verification.verify(ctx.message)


@bot.command()
async def getcode(ctx):
    await verification.send_code(ctx.message)


@bot.command()
async def roll(ctx):
    # TODO: use
    # https://discordpy.readthedocs.io/en/latest/ext/commands/commands.html#basic-converters
    # and only pass integers to the function?
    await ctx.send(rng.generate_number(ctx.message))
    await botroom_check(ctx.message)


@bot.command()
async def flip(ctx):
    await ctx.send(rng.flip())
    await botroom_check(ctx.message)


@bot.command()
async def week(ctx):
    await ctx.send(rng.week())


@bot.command()
async def pick(ctx):
    """"Pick an option"""
    option = rng.pick_option(ctx.message)
    if option:
        await ctx.send("{} {}"
                       .format(option,
                               utils.generate_mention(
                                   ctx.author.id)))
    await botroom_check(ctx.message)


@bot.command(name="karma")
async def pick_karma_command(ctx, *args):
    if len(args) == 0:
        await karma.karma_get(ctx.message)
        await botroom_check(ctx.message)

    elif args[0] == "get":
        if not await guild_check(ctx.message):
            await ctx.send(
                "{}".format(messages.server_warning))
        else:
            try:
                await karma.emoji_get_value(ctx.message)
                await botroom_check(ctx.message)
            except discord.errors.Forbidden:
                return

    elif args[0] == "revote":
        if not await guild_check(ctx.message):
            await ctx.send(
                "{}".format(messages.server_warning))
        else:
            if ctx.message.channel.id == config.vote_room:
                try:
                    await ctx.message.delete()
                    await karma.emoji_revote_value(ctx.message)
                except discord.errors.Forbidden:
                    return
            else:
                await ctx.send(
                    messages.vote_room_only
                    .format(room=discord.utils.get(ctx.guild.channels,
                                                   id=config.vote_room)))

    elif args[0] == "vote":
        if not await guild_check(ctx.message):
            await ctx.send(
                "{}".format(messages.server_warning))
        else:
            if ctx.message.channel.id == config.vote_room:
                try:
                    await ctx.message.delete()
                    await karma.emoji_vote_value(ctx.message)
                except discord.errors.Forbidden:
                    return
            else:
                await ctx.send(
                    messages.vote_room_only
                    .format(room=discord.utils.get(ctx.guild.channels,
                                                   id=config.vote_room)))

    elif args[0] == "given":
        await karma.karma_giving_get(ctx.message)
        await botroom_check(ctx.message)

    elif args[0] == "give":
        if ctx.author.id == config.admin_id:
            await karma.karma_give(ctx.message)
        else:
            await ctx.send(
                messages.insufficient_rights
                .format(user=utils.generate_mention(ctx.author.id)))
    else:
        await ctx.send(
            messages.karma_invalid_command
            .format(utils.generate_mention(ctx.author.id)))


@bot.command()
async def leaderboard(ctx):
    await karma.leaderboard(ctx.message.channel, 'get', 'DESC')
    await botroom_check(ctx.message)


@bot.command()
async def bajkarboard(ctx):
    await karma.leaderboard(ctx.message.channel, 'get', 'ASC')
    await botroom_check(ctx.message)


@bot.command()
async def givingboard(ctx):
    await karma.leaderboard(ctx.message.channel, 'give', 'DESC')
    await botroom_check(ctx.message)


@bot.command()
async def ishaboard(ctx):
    await karma.leaderboard(ctx.message.channel, 'give', 'ASC')
    await botroom_check(ctx.message)


@bot.command()
async def god(ctx):
    embed = discord.Embed(title="Rubbergod",
                          description="Nejlepší a nejúžasnější bot ever. "
                                      "Autor, počet serverů "
                                      "a dostupné příkazy jsou:",
                          color=0xeee657)

    prefix = config.command_prefix

    # give info about you here
    embed.add_field(name="Author", value="Toaster#1111")

    # Shows the number of servers the bot is member of.
    embed.add_field(name="Počet serverů s touto instancí bota",
                    value=f"{len(bot.guilds)}")

    for command in messages.info:
        embed.add_field(name=prefix + command[0],
                        value=command[1],
                        inline=False)

    await ctx.send(embed=embed)


@bot.command()
async def diceroll(ctx, *, arg=""):
    await ctx.send(roll_dice.roll_dice(arg))
    await botroom_check(ctx.message)


bot.run(config.key)
