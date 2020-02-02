import discord
from discord.ext import commands

from config import config, messages
from features import review
from repository import review_repo
import utils

config = config.Config
messages = messages.Messages
review_repo = review_repo.ReviewRepository()


class Review(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.rev = review.Review(bot)

    @commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)
    @commands.command()
    async def reviews(self, ctx, subcommand=None, subject=None,
                      tier: int = None, *args):
        if subcommand is None:
            await ctx.send(messages.review_format)
        else:
            if isinstance(ctx.message.channel, discord.DMChannel):
                guild = self.bot.get_guild(config.guild_id)
                roles = guild.get_member(ctx.message.author.id).roles
            else:
                roles = ctx.message.author.roles
            if subcommand == 'add':
                for role in roles:
                    if role.name in config.reviews_forbidden_roles:
                        await ctx.send(utils.fill_message("review_add_denied",
                                       user=ctx.message.author.id))
                        return
                if subject is None or tier is None:
                    await ctx.send(messages.review_add_format)
                    return
                author = ctx.message.author.id
                anonym = False
                if tier < 0 or tier > 4:
                    await ctx.send(messages.review_tier)
                    return
                if args:
                    if args[0] == "anonym":
                        anonym = True
                        args = args[1:]
                    args = ' '.join(args)
                args_len = len(args)
                if args_len == 0:
                    args = None
                try:
                    self.rev.add_review(author, subject.lower(), tier, anonym, args)
                except Exception:
                    await ctx.send(messages.review_wrong_subject)
                    return
                await ctx.send(messages.review_added)
            elif subcommand == 'remove':
                if subject is None:
                    if ctx.author.id == config.admin_id:
                        await ctx.send(messages.review_remove_format_admin)
                    else:
                        await ctx.send(messages.review_remove_format)
                elif subject == 'id':
                    if ctx.author.id == config.admin_id:
                        if tier is None:
                            await ctx.send(messages.review_remove_id_format)
                        else:
                            review_repo.remove(tier) # tier => ID of review
                            await ctx.send(messages.review_remove_success)
                    else:
                        await ctx.send(utils.fill_message("insufficient_rights", user=ctx.author.id))
                else:
                    subject = subject.lower()
                    if self.rev.remove(str(ctx.message.author.id), subject):
                        await ctx.send(messages.review_remove_success)
                    else:
                        await ctx.send(messages.review_remove_error)
            else:
                subject = subcommand
                embed = self.rev.list_reviews(subject.lower())
                if not embed:
                    await ctx.send(messages.review_wrong_subject)
                    return
                msg = await ctx.send(embed=embed)
                footer = msg.embeds[0].footer.text.split('|')[0]
                if msg.embeds[0].description[-1].isnumeric():
                    if footer != "Review: 1/1 ":
                        await msg.add_reaction("⏪")
                        await msg.add_reaction("◀")
                        await msg.add_reaction("▶")
                    await msg.add_reaction("👍")
                    await msg.add_reaction("🛑")
                    await msg.add_reaction("👎")
                    if msg.embeds[0].fields[3].name == "Text page":
                        await msg.add_reaction("🔼")
                        await msg.add_reaction("🔽")

    @reviews.error
    async def review_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(messages.review_add_format)

    @commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)
    @commands.command()
    async def subject(self, ctx, subcommand=None, subject=None):
        if ctx.author.id == config.admin_id:
            if not subcommand or not subject:
                await ctx.send(messages.subject_format)
                return
            subject = subject.lower()
            if subcommand == "add":
                self.rev.add_subject(subject)
                await ctx.send(f'Zkratka {subject} byla přidána')
            elif subcommand == "remove":
                self.rev.remove_subject(subject)
                await ctx.send(f'Zkratka {subject} byla odebrána')
            else:
                await ctx.send(messages.review_wrong_subject)
        else:
            await ctx.send(utils.fill_message("insufficient_rights", user=ctx.author.id))


def setup(bot):
    bot.add_cog(Review(bot))
