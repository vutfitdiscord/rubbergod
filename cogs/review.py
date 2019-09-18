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
            for role in ctx.message.author.roles:
                if "MUNI" == role.name or "Host" == role.name:
                    await ctx.send(messages.review_add_denied.format(
                                   user=ctx.message.author.mention))
                    return
            if subcommand == 'add':
                if subject is None or tier is None:
                    await ctx.send(messages.review_add_format)
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
                    self.rev.add_review(author, subject, tier, anonym, args)
                except:
                    await ctx.send(messages.review_wrong_subject)
                    return
                await ctx.send(messages.review_added)
            elif subcommand == 'remove':
                if subject is None:
                    await ctx.send(messages.review_remove_format)
                elif subject == 'id':
                    if ctx.author.id == config.admin_id:
                        if tier is None:
                            await ctx.send(messages.review_remove_id_format)
                        else:
                            review_repo.remove(tier)
                            await ctx.send(messages.review_remove_success)
                    else:
                        await ctx.send(messages.insufficient_rights.format(
                                user=utils.generate_mention(ctx.author.id)))
                else:
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
                if msg.embeds[0].description[-1].isnumeric():
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
            await ctx.send(messages.review_format)

    @commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)
    @commands.command()
    async def subject(self, ctx, subcommand=None, subject=None):
        if ctx.author.id == config.admin_id:
            if not subcommand or not subject:
                await ctx.send(messages.subject_format)
                return
            if subcommand == "add":
                self.rev.add_subject(subject)
                await ctx.send(f'Zkratka {subject} byla přidána')
            elif subcommand == "remove":
                self.rev.remove_subject(subject)
                await ctx.send(f'Zkratka {subject} byla odebrána')
            else:
                await ctx.send(messages.review_wrong_subject)
        else:
            await ctx.send(
                messages.insufficient_rights
                .format(user=utils.generate_mention(ctx.author.id)))


def setup(bot):
    bot.add_cog(Review(bot))
