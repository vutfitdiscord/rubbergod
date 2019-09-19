from discord.ext import commands

from features import vote


class Vote(commands.Cog):
    def __init__(self, bot, karma):
        self.bot = bot
        self.karma_cog = karma
        self.voter = vote.Vote(bot)
        karma.reaction.use_voter(self.voter)

    @commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)
    @commands.command()
    async def vote(self, ctx):
        await self.voter.handle_vote(ctx)


def setup(bot):
    bot.add_cog(Vote(bot, bot.get_cog("Karma")))
