import datetime
import traceback
from random import choice

import discord
from discord.ext import commands

import utils
from config import config, messages
from features import (karma, presence, verification, reaction)
from logic import roll_dice, rng
from repository import (karma_repo, user_repo)

config = config.Config
messages = messages.Messages

bot = commands.Bot(command_prefix=commands.when_mentioned_or(
                                      *config.command_prefix),
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

arcas_time = (datetime.datetime.utcnow() -
              datetime.timedelta(hours=config.arcas_delay))
boottime = datetime.datetime.now().replace(microsecond=0)
uhoh_counter = 0


async def botroom_check(message):
    room = await get_room(message)
    if room is not None and room.id not in config.allowed_channels:
        await message.channel.send(messages.bot_room_redirect.format(
            utils.generate_mention(message.author.id),
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
    global uhoh_counter

    if message.author.bot:
        return

    if message.content.startswith(config.role_string):
        role_data = await reaction.get_join_role_data(message)
        await reaction.message_role_reactions(message, role_data)
    elif message.content.lower() == "uh oh":
        await message.channel.send("uh oh")
        uhoh_counter += 1
    else:
        await bot.process_commands(message)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.BadArgument) and ctx.command.name == 'hug':
        return

    if isinstance(error, commands.CommandNotFound):
        if not ctx.message.content.startswith('!'):
            await ctx.send(messages.no_such_command)
        return
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(messages.spamming.format(
            user=utils.generate_mention(ctx.author.id)
            ))
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
    if arcas_time + datetime.timedelta(hours=config.arcas_delay) < when and \
            config.arcas_id == user.id:
        arcas_time = when
        gif = discord.Embed()
        gif.set_image(url="https://i.imgur.com/v2ueHcl.gif")
        await channel.send(embed=gif)


#                                      #
#              COMMANDS                #
#                                      #

@commands.cooldown(rate=2, per=20.0, type=commands.BucketType.user)
@bot.command()
async def uhoh(ctx):
    await ctx.send(messages.uhoh_counter.format(uhohs=uhoh_counter))


@commands.cooldown(rate=2, per=20.0, type=commands.BucketType.user)
@bot.command()
async def uptime(ctx):
    now = datetime.datetime.now().replace(microsecond=0)
    delta = now - boottime
    await ctx.send(
            messages.uptime_message
            .format(boottime=str(boottime), uptime=str(delta))
            )


@commands.cooldown(rate=5, per=30.0, type=commands.BucketType.user)
@bot.command()
async def verify(ctx):
    await verification.verify(ctx.message)


@commands.cooldown(rate=5, per=30.0, type=commands.BucketType.user)
@bot.command()
async def getcode(ctx):
    await verification.send_code(ctx.message)


@commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)
@bot.command()
async def roll(ctx):
    # TODO: use
    # https://discordpy.readthedocs.io/en/latest/ext/commands/commands.html#basic-converters
    # and only pass integers to the function?
    await ctx.send(rng.generate_number(ctx.message))
    await botroom_check(ctx.message)


@commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)
@bot.command()
async def flip(ctx):
    await ctx.send(rng.flip())
    await botroom_check(ctx.message)


@commands.cooldown(rate=2, per=20.0, type=commands.BucketType.user)
@bot.command()
async def week(ctx):
    await ctx.send(rng.week())


@commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)
@bot.command()
async def pick(ctx, *args):
    """"Pick an option"""
    option = rng.pick_option(' '.join(args))
    if option:
        await ctx.send("{} {}"
                       .format(option,
                               utils.generate_mention(
                                   ctx.author.id)))
    await botroom_check(ctx.message)


# TODO: split the karma commands so that we can cooldown them separately?
@commands.cooldown(rate=5, per=30.0, type=commands.BucketType.user)
@bot.command(name="karma")
async def pick_karma_command(ctx, *args):
    if len(args) == 0:
        await ctx.send(karma.karma_get(ctx.author))
        await botroom_check(ctx.message)

    elif args[0] == "stalk":
        try:
            converter = commands.MemberConverter()
            target_member = await converter.convert(
                    ctx=ctx, argument=' '.join(args[1:]))
        except commands.errors.BadArgument:
            await ctx.send(
                messages.member_not_found
                .format(user=utils.generate_mention(ctx.author.id)))
            return

        await ctx.send(
            messages.karma_stalk.format(
                user=utils.generate_mention(ctx.author.id),
                target=target_member.display_name,
                karma=''.join(karma.karma_get(target_member
                                              ).split(':')[1:]),
                karma_given='\n'.join(
                    karma.karma_giving_get(target_member
                                           ).split('\n')[1:])
                )
            )
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
            if ctx.message.channel.id == config.vote_room or \
               ctx.author.id == config.admin_id:
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
            if ctx.message.channel.id == config.vote_room or \
               ctx.author.id == config.admin_id:
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
        await ctx.send(karma.karma_giving_get(ctx.author))
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


@commands.cooldown(rate=2, per=30.0, type=commands.BucketType.user)
@bot.command()
async def leaderboard(ctx):
    await karma.leaderboard(ctx.message.channel, 'get', 'DESC')
    await botroom_check(ctx.message)


@commands.cooldown(rate=2, per=30.0, type=commands.BucketType.user)
@bot.command()
async def bajkarboard(ctx):
    await karma.leaderboard(ctx.message.channel, 'get', 'ASC')
    await botroom_check(ctx.message)


@commands.cooldown(rate=2, per=30.0, type=commands.BucketType.user)
@bot.command()
async def givingboard(ctx):
    await karma.leaderboard(ctx.message.channel, 'give', 'DESC')
    await botroom_check(ctx.message)


@commands.cooldown(rate=2, per=30.0, type=commands.BucketType.user)
@bot.command()
async def ishaboard(ctx):
    await karma.leaderboard(ctx.message.channel, 'give', 'ASC')
    await botroom_check(ctx.message)


@commands.cooldown(rate=2, per=60.0, type=commands.BucketType.user)
@bot.command()
async def god(ctx):
    embed = reaction.make_embed(1)

    channel = await get_room(ctx.message)
    if channel is not None and channel.id != config.bot_room:
        try:
            msg = await ctx.author.send(embed=embed)
            await ctx.message.delete()
        except discord.errors.Forbidden:
            return
    else:
        msg = await ctx.send(embed=embed)
    await msg.add_reaction("⏩")


@commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)
@bot.command()
async def diceroll(ctx, *, arg=""):
    await ctx.send(roll_dice.roll_dice(arg))
    await botroom_check(ctx.message)


@commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)
@bot.command()
async def hug(ctx, user: discord.Member = None, intensity: int = 0):
    """Because everyone likes hugs"""
    if user is None:
        user = ctx.author
    elif user == bot.user:
        await ctx.send("<:huggers:602823825880514561>")
        return

    emojis = config.hug_emojis

    user = discord.utils.escape_markdown(user.display_name)
    if 0 <= intensity < len(emojis):
        await ctx.send(emojis[intensity] + f" **{user}**")
    else:
        await ctx.send(choice(emojis) + f" **{user}**")


@hug.error
async def hug_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        await ctx.send(
            messages.member_not_found
            .format(user=utils.generate_mention(ctx.author.id)))


bot.run(config.key)
