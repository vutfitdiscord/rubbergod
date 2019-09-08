import discord
from discord.ext import commands

from config import config, messages
from features import review

config = config.Config

class Review(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.rev = review.Review(bot)

    @commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)
    @commands.command()
    async def review(self, ctx, subject=None, tier=None, *args):
        if subject is None or tier is None:
            await ctx.send("?review nazov_predmetu tier \nrecenzia")
        else:
            author = ctx.message.author.id
            anonym = False
            print(args)
            if args is not None:
                if args[0] == "anonym":
                    anonym = True
                    args = args[1:]
                args = ' '.join(args)
            if len(args) == 0:
                args = None
            self.rev.add_review(author_id=author, subject=subject, tier=tier, anonym=anonym, text=args)
            await ctx.send("Hodnotenie predmetu bolo pridane")

    @commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)
    @commands.command()
    async def get_reviews(self, ctx, subject=None):
        if subject is None:
            await ctx.send("Pls napis aky predmet")
        else:
            embed = self.rev.list_reviews(subject)
            await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Review(bot))
