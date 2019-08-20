import discord
from discord.ext import commands

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
    async def role_check(self, ctx):
        if ctx.author.id != config.admin_id:
            await ctx.send(
                    messages.insufficient_rights
                    .format(user=utils.generate_mention(ctx.author.id)))
            return

        guild = self.bot.get_guild(config.guild_id)
        members = guild.members

        verify = discord.utils.get(guild.roles, name="Verify")
        host = discord.utils.get(guild.roles, name="Host")

        verified = [member for member in members
                    if verify in member.roles and host not in member.roles]

        permited = session.query(Permit)
        permited_ids = [person.discord_ID for person in permited]

        for member in verified:
            if member.id not in permited_ids:
                await ctx.send("Nenasel jsem v verified databazi: " +
                               member.display_name)
            else:
                login = session.query(Permit).\
                    filter(Permit.discord_ID == member.id).one().login

                person = session.query(Valid_person).\
                    filter(Valid_person.login == login).one()

                if person.status != 0:
                    await ctx.send("Status nesedi u: " + login)

                year = self.verification.transform_year(person.year)

                role = discord.utils.get(guild.roles, name=year)

                if role not in member.roles:
                    await ctx.send("Role nesedi u: " + member.display_name +
                                   ", mel by mit roli: " + year)


def setup(bot):
    bot.add_cog(Verify(bot))
