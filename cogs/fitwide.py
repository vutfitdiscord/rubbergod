import datetime
from sqlalchemy.orm.exc import NoResultFound

import discord
from discord.ext import commands


import utils
from config import config, messages
from features import verification
from repository import user_repo
from repository.database import database, session
from repository.database.verification import Valid_person, Permit
from repository.database.year_increment import User_backup

user_r = user_repo.UserRepository()

config = config.Config
messages = messages.Messages
arcas_time = (datetime.datetime.utcnow() -
              datetime.timedelta(hours=config.arcas_delay))


class FitWide(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.verification = verification.Verification(bot, user_r)

    @commands.Cog.listener()
    async def on_typing(self, channel, user, when):
        global arcas_time
        if arcas_time + datetime.timedelta(hours=config.arcas_delay) <\
           when and config.arcas_id == user.id:
            arcas_time = when
            gif = discord.Embed()
            gif.set_image(url="https://i.imgur.com/v2ueHcl.gif")
            await channel.send(embed=gif)

    @commands.cooldown(rate=2, per=20.0, type=commands.BucketType.user)
    @commands.command()
    async def role_check(self, ctx, p_verified: bool = True,
                         p_move: bool = True, p_status: bool = True,
                         p_role: bool = True, p_muni: bool = True):
        if ctx.author.id != config.admin_id:
            await ctx.send(
                    messages.insufficient_rights
                    .format(user=utils.generate_mention(ctx.author.id)))
            return

        guild = self.bot.get_guild(config.guild_id)
        members = guild.members

        verify = discord.utils.get(guild.roles, name="Verify")
        host = discord.utils.get(guild.roles, name="Host")
        bot = discord.utils.get(guild.roles, name="Bot")
        poradce = discord.utils.get(guild.roles, name="Poradce")
        dropout = discord.utils.get(guild.roles, name="Dropout")
        muni = discord.utils.get(guild.roles, name="MUNI")

        verified = [member for member in members
                    if verify in member.roles and
                    host not in member.roles and
                    bot not in member.roles and
                    dropout not in member.roles and
                    poradce not in member.roles]

        if not p_muni:
            verified = [member for member in verified
                        if muni not in member.roles]

        permited = session.query(Permit)
        permited_ids = [int(person.discord_ID) for person in permited]

        bit0 = discord.utils.get(guild.roles, name="0BIT")
        bit1 = discord.utils.get(guild.roles, name="1BIT")
        bit2 = discord.utils.get(guild.roles, name="2BIT")
        bit3 = discord.utils.get(guild.roles, name="3BIT")
        bit4 = discord.utils.get(guild.roles, name="4BIT+")
        mit1 = discord.utils.get(guild.roles, name="1MIT")

        for member in verified:
            if member.id not in permited_ids:
                if p_verified:
                    await ctx.send("Nenasel jsem v verified databazi: " +
                                   utils.generate_mention(member.id))
            else:
                try:
                    login = session.query(Permit).\
                        filter(Permit.discord_ID == str(member.id)).one().login

                    person = session.query(Valid_person).\
                        filter(Valid_person.login == login).one()
                except NoResultFound:
                    continue

                if person.status != 0:
                    if p_status:
                        await ctx.send("Status nesedi u: " + login)

                year = self.verification.transform_year(person.year)

                role = discord.utils.get(guild.roles, name=year)

                if role not in member.roles:
                    if year == "1MIT" and bit4 in member.roles and p_move:
                        await member.add_roles(mit1)
                        await member.remove_roles(bit4)
                        await ctx.send("Presouvam: " + member.display_name +
                                       " do 1MIT")
                    elif year == "4BIT+" and bit3 in member.roles and p_move:
                        await member.add_roles(bit4)
                        await member.remove_roles(bit3)
                        await ctx.send("Presouvam: " + member.display_name +
                                       " do 4BIT+")
                    elif year == "3BIT" and bit2 in member.roles and p_move:
                        await member.add_roles(bit3)
                        await member.remove_roles(bit2)
                        await ctx.send("Presouvam: " + member.display_name +
                                       " do 3BIT")
                    elif year == "2BIT" and bit1 in member.roles and p_move:
                        await member.add_roles(bit2)
                        await member.remove_roles(bit1)
                        await ctx.send("Presouvam: " + member.display_name +
                                       " do 2BIT")
                    elif year == "1BIT" and bit0 in member.roles and p_move:
                        await member.add_roles(bit1)
                        await member.remove_roles(bit0)
                        await ctx.send("Presouvam: " + member.display_name +
                                       " do 1BIT")
                    elif not p_role:
                        continue
                    elif year is None:
                        await ctx.send("Nesedi mi role u: " +
                                       utils.generate_mention(member.id) +
                                       ", ma ted rocnik: " + person.year)
                    else:
                        await ctx.send("Nesedi mi role u: " +
                                       utils.generate_mention(member.id) +
                                       ", mel by mit roli: " + year)

        await ctx.send("Done")

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
    bot.add_cog(FitWide(bot))
