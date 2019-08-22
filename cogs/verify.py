import discord
from discord.ext import commands
from sqlalchemy.orm.exc import NoResultFound
import utils
from config import config, messages
from features import verification
from repository import user_repo
from repository.database import session
from repository.database.verification import Valid_person, Permit

user_r = user_repo.UserRepository()

config = config.Config


class Verify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.verification = verification.Verification(bot, user_r)

    @commands.cooldown(rate=5, per=30.0, type=commands.BucketType.user)
    @commands.command()
    async def verify(self, ctx):
        await self.verification.verify(ctx.message)

    @commands.cooldown(rate=5, per=30.0, type=commands.BucketType.user)
    @commands.command()
    async def getcode(self, ctx):
        await self.verification.send_code(ctx.message)

    @commands.cooldown(rate=2, per=20.0, type=commands.BucketType.user)
    @commands.command()
    async def role_check(self, ctx, p_verified: bool=True, p_move: bool=True,
                         p_status: bool=True, p_role: bool=True):
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

        verified = [member for member in members
                    if verify in member.roles and
                    host not in member.roles and 
                    bot not in member.roles and 
                    dropout not in member.roles and 
                    poradce not in member.roles]

        permited = session.query(Permit)
        permited_ids = [int(person.discord_ID) for person in permited]

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

                bit4 = discord.utils.get(guild.roles, name="4BIT+")
                mit1 = discord.utils.get(guild.roles, name="1MIT")

                if role not in member.roles:
                    if year == "1MIT" and bit4 in member.roles and p_move:
                        await member.add_roles(mit1)
                        await member.remove_roles(bit4)
                        await ctx.send("Presouvam: " + member.display_name +
                                       "na magisterske studium")
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

def setup(bot):
    bot.add_cog(Verify(bot))
