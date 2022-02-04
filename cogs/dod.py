from discord import Member
from discord.ext import commands
from config.app_config import config
from config.messages import Messages
from features import verification
from repository import user_repo
import discord
import utils


user_r = user_repo.UserRepository()


class Dod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.verification = verification.Verification(bot, user_r)

    async def has_role(self, user, role_name):
        if type(user) == Member:
            return utils.has_role(user, role_name)
        else:
            guild = await self.bot.fetch_guild(config.guild_id)
            member = await guild.fetch_member(user.id)
            return utils.has_role(member, role_name)

    @commands.cooldown(rate=5, per=30.0, type=commands.BucketType.user)
    @commands.command()
    async def dod(self, ctx):
        # Check if the user doesn't have the verify role
        if not await self.has_role(ctx.author, config.verification_role):
            embed = discord.Embed(title="DOD verify",
                                  color=0xeee657)
            embed.add_field(name="User", value=utils.generate_mention(ctx.author.id))
            channel = self.bot.get_channel(config.log_channel)
            await channel.send(embed=embed)
            try:
                # Get server verify role
                verify = discord.utils.get(
                    ctx.message.guild.roles,
                    name=config.verification_role)
                DOD = discord.utils.get(ctx.message.guild.roles, name="DOD")
                host = discord.utils.get(ctx.message.guild.roles, name="Host")
                zajemce = discord.utils.get(ctx.message.guild.roles, name="ZajemceoStudium")
                member = ctx.author
            except AttributeError:
                # jsme v PM
                guild = self.bot.get_guild(config.guild_id)
                verify = discord.utils.get(
                    guild.roles,
                    name=config.verification_role)
                DOD = discord.utils.get(ctx.message.guild.roles, name="DOD")
                host = discord.utils.get(ctx.message.guild.roles, name="Host")
                zajemce = discord.utils.get(ctx.message.guild.roles, name="ZajemceoStudium")
                member = guild.get_member(ctx.author.id)

            await member.add_roles(verify)
            await member.add_roles(DOD)
            await member.add_roles(host)
            await member.add_roles(zajemce)

            await member.send(utils.fill_message("verify_verify_success",
                                                 user=ctx.author.id))

            await member.send(Messages.verify_post_verify_info)

            if ctx.message.channel.type is not discord.ChannelType.private:
                await ctx.message.channel.send(utils.fill_message("verify_verify_success",
                                               user=ctx.author.id))
        else:
            await ctx.send(utils.fill_message("verify_already_verified",
                                       user=ctx.author.id, admin=config.admin_ids[0]))
        try:
            await ctx.message.delete()
        except discord.errors.Forbidden:
            return


def setup(bot):
    bot.add_cog(Dod(bot))
