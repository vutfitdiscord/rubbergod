import datetime
import traceback

import discord
from discord.ext import commands

import utils
from config import config, messages
from logic import rng
from features import reaction
from repository import karma_repo
from cogs import room_check

from repository.database import database, session
from repository.database.verification import Valid_person
from repository.database.year_increment import User_backup

rng = rng.Rng()
config = config.Config
messages = messages.Messages
karma_r = karma_repo.KarmaRepository()

boottime = datetime.datetime.now().replace(microsecond=0)


class Base(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.reaction = reaction.Reaction(bot, karma_r)
        self.check = room_check.RoomCheck(bot)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.BadArgument) and \
           ctx.command.name == 'hug':
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
            channel = self.bot.get_channel(config.bot_dev_channel)
            print(output)
            if channel is not None:
                await channel.send("```\n" + output + "\n```")

    @commands.cooldown(rate=2, per=20.0, type=commands.BucketType.user)
    @commands.command()
    async def uptime(self, ctx):
        now = datetime.datetime.now().replace(microsecond=0)
        delta = now - boottime
        await ctx.send(
                messages.uptime_message
                .format(boottime=str(boottime), uptime=str(delta))
                )

    @commands.cooldown(rate=2, per=20.0, type=commands.BucketType.user)
    @commands.command()
    async def week(self, ctx):
        await ctx.send(rng.week())

    @commands.cooldown(rate=2, per=60.0, type=commands.BucketType.user)
    @commands.command()
    async def god(self, ctx):
        embed = self.reaction.make_embed(1)

        channel = await self.check.get_room(ctx.message)
        if channel is not None and channel.id != config.bot_room:
            try:
                msg = await ctx.author.send(embed=embed)
                await ctx.message.delete()
            except discord.errors.Forbidden:
                return
        else:
            msg = await ctx.send(embed=embed)
        await msg.add_reaction("▶")

    @commands.cooldown(rate=2, per=20.0, type=commands.BucketType.user)
    @commands.command()
    async def increment_roles(self, ctx):
        if ctx.author.id != config.admin_id:
            await ctx.send(
                    messages.insufficient_rights
                    .format(user=utils.generate_mention(ctx.author.id)))
            return

        database.base.metadata.create_all(database.db)

        guild = self.bot.get_guild(config.guild_id)

        BIT_names = [str(x) + "BIT" + ("+" if x == 4 else "")
                     for x in range(5)]
        BIT = [discord.utils.get(guild.roles, name=role_name)
               for role_name in BIT_names]

        MIT_names = [str(x) + "MIT" + ("+" if x == 3 else "")
                     for x in range(4)]
        MIT = [discord.utils.get(guild.roles, name=role_name)
               for role_name in MIT_names]

        # pridat kazdeho 3BIT a 2MIT cloveka do DB pred tim nez je jebnem do
        # 4BIT+ respektive 3MIT+ role kvuli rollbacku
        session.query(User_backup).delete()

        for member in BIT[3].members:
            session.add(User_backup(member_ID=member.id))
        for member in MIT[2].members:
            session.add(User_backup(member_ID=member.id))

        session.commit()

        for member in BIT[3].members:
            await member.add_roles(BIT[4])
        for member in MIT[2].members:
            await member.add_roles(MIT[3])

        BIT_colors = [role.color for role in BIT]
        await BIT[3].delete()
        await BIT[2].edit(name="3BIT", color=BIT_colors[3])
        await BIT[1].edit(name="2BIT", color=BIT_colors[2])
        await BIT[0].edit(name="1BIT", color=BIT_colors[1])
        bit0 = await guild.create_role(name='0BIT', color=BIT_colors[0])
        await bit0.edit(position=BIT[0].position - 1)

        MIT_colors = [role.color for role in MIT]
        await MIT[2].delete()
        await MIT[1].edit(name="2MIT", color=MIT_colors[2])
        await MIT[0].edit(name="1MIT", color=MIT_colors[1])
        mit0 = await guild.create_role(name='0MIT', color=MIT_colors[0])
        await mit0.edit(position=MIT[0].position - 1)

        general_names = [str(x) + "bit-general" for x in range(4)]
        terminy_names = [str(x) + "bit-terminy" for x in range(1, 3)]
        general_channels = [discord.utils.get(guild.channels,
                                              name=channel_name)
                            for channel_name in general_names]
        terminy_channels = [discord.utils.get(guild.channels,
                                              name=channel_name)
                            for channel_name in terminy_names]
        # TODO: do smth about 4bit general next year, delete it in the meantime
        bit4_general = discord.utils.get(guild.channels, name="4bit-general")
        if bit4_general is not None:
            await bit4_general.delete()

        # move names
        await general_channels[3].edit(name="4bit-general")
        await general_channels[2].edit(name="3bit-general")
        await general_channels[1].edit(name="2bit-general")
        await general_channels[0].edit(name="1bit-general")
        # create 0bit-general
        overwrites = {
            guild.default_role:
                discord.PermissionOverwrite(read_messages=False),
            discord.utils.get(guild.roles, name="0BIT"):
                discord.PermissionOverwrite(read_messages=True,
                                            send_messages=True)
        }
        await guild.create_text_channel(
                '0bit-general', overwrites=overwrites,
                category=general_channels[0].category,
                position=general_channels[0].position - 1
        )

        # delete 3bit-terminy
        await discord.utils.get(guild.channels, name="3bit-terminy").delete()

        await terminy_channels[1].edit(name="3bit-terminy")
        await terminy_channels[0].edit(name="2bit-terminy")
        # create 1bit-terminy
        overwrites = {
            guild.default_role:
                discord.PermissionOverwrite(read_messages=False),
            discord.utils.get(guild.roles, name="1BIT"):
                discord.PermissionOverwrite(read_messages=True,
                                            send_messages=False)
        }
        await guild.create_text_channel(
                '1bit-terminy', overwrites=overwrites,
                category=terminy_channels[0].category,
                position=terminy_channels[0].position - 1
        )

        # give 4bit perms to the new 3bit terminy
        await terminy_channels[1].set_permissions(
            discord.utils.get(guild.roles, name="4BIT+"),
            read_messages=True, send_messages=False
        )

        # Give people the correct mandatory classes after increment
        semester_names = [str(x) + ". Semestr" for x in range(1, 6)]
        semester = [discord.utils.get(guild.categories, name=semester_name)
                    for semester_name in semester_names]
        await semester[0].set_permissions(discord.utils.get(guild.roles,
                                                            name="1BIT"),
                                          read_messages=True,
                                          send_messages=True)
        await semester[0].set_permissions(discord.utils.get(guild.roles,
                                                            name="2BIT"),
                                          overwrite=None)
        await semester[1].set_permissions(discord.utils.get(guild.roles,
                                                            name="1BIT"),
                                          read_messages=True,
                                          send_messages=True)
        await semester[1].set_permissions(discord.utils.get(guild.roles,
                                                            name="2BIT"),
                                          overwrite=None)
        await semester[2].set_permissions(discord.utils.get(guild.roles,
                                                            name="2BIT"),
                                          read_messages=True,
                                          send_messages=True)
        await semester[2].set_permissions(discord.utils.get(guild.roles,
                                                            name="3BIT"),
                                          overwrite=None)
        await semester[3].set_permissions(discord.utils.get(guild.roles,
                                                            name="2BIT"),
                                          read_messages=True,
                                          send_messages=True)
        await semester[3].set_permissions(discord.utils.get(guild.roles,
                                                            name="3BIT"),
                                          overwrite=None)
        await semester[4].set_permissions(discord.utils.get(guild.roles,
                                                            name="3BIT"),
                                          read_messages=True,
                                          send_messages=True)

        await ctx.send('Holy fuck, vsechno se povedlo, '
                       'tak zase za rok <:Cauec:602052606210211850>')

    # TODO: the opposite of increment_roles (for rollback and testing)
    # and role_check to check if peoples roles match the database

    @commands.cooldown(rate=2, per=20.0, type=commands.BucketType.user)
    @commands.command()
    async def update_db(self, ctx):
        if ctx.author.id != config.admin_id:
            await ctx.send(
                    messages.insufficient_rights
                    .format(user=utils.generate_mention(ctx.author.id)))
            return

        with open("merlin-latest", "r") as f:
            data = f.readlines()

        new_people = []
        new_logins = []

        for line in data:
            line = line.split(":")
            login = line[0]
            name = line[4].split(",", 1)[0]
            try:
                year = line[4].split(",")[1]
            except IndexError:
                continue
            new_people.append(Valid_person(login=login, year=year,
                                           name=name))
            new_logins.append(login)

        for person in new_people:
            session.merge(person)

        for person in session.query(Valid_person):
            if person.login not in new_logins:
                try:
                    # check for muni
                    int(person.login)
                    print("Muni pls")
                    person.year = "MUNI"
                except ValueError:
                    person.year = "dropout"

        session.commit()
        
        await ctx.send("Update databaze probehl uspesne")


def setup(bot):
    bot.add_cog(Base(bot))
