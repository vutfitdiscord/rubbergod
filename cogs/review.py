from discord.ext import commands

from config import config, messages
from features import review
import utils

config = config.Config
messages = messages.Messages


class Review(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.rev = review.Review(bot)

    @commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)
    @commands.command()
    async def review(self, ctx, subject=None, tier: int = None, *args):
        if subject is None or tier is None:
            await ctx.send(messages.review_format)
        else:
            author = ctx.message.author.id
            anonym = False
            if tier < 0 or tier > 3:
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
            elif args_len > 1024:
                await ctx.send(messages.review_text_len)
                return
            try:
                self.rev.add_review(author, subject, tier, anonym, args)
            except:
                await ctx.send(messages.review_wrong_subject)
                return
            await ctx.send(messages.review_added)

    @review.error
    async def review_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(messages.review_format)

    @commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)
    @commands.command()
    async def get_reviews(self, ctx, subject: str = None):
        if subject is None:
            await ctx.send(messages.review_get_format)
        else:
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
                await msg.add_reaction("👎")

    @commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)
    @commands.command()
    async def add_subject(self, ctx, subject=None):
        if ctx.author.id == config.admin_id:
            if not subject:
                await ctx.send(messages.review_wrong_subject)
                return
            self.rev.add_subject(subject)
            await ctx.send(f'Zkratka {subject} byla přidána')
        else:
            await ctx.send(
                messages.insufficient_rights
                .format(user=utils.generate_mention(ctx.author.id)))

    @commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)
    @commands.command()
    async def remove_subject(self, ctx, subject=None):
        if ctx.author.id == config.admin_id:
            if not subject:
                await ctx.send(messages.review_wrong_subject)
                return
            self.rev.remove_subject(subject)
            await ctx.send(f'Zkratka {subject} byla odebrána')
        else:
            await ctx.send(
                messages.insufficient_rights
                .format(user=utils.generate_mention(ctx.author.id)))


def setup(bot):
    bot.add_cog(Review(bot))
