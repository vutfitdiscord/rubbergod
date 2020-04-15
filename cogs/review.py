import discord
from datetime import datetime
from discord.ext import commands

from config import config, messages
from repository import review_repo
import utils

config = config.Config
messages = messages.Messages
review_repo = review_repo.ReviewRepository()

class Review(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.rev = Review_helper(bot)

    @commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)
    @commands.command()
    async def reviews(self, ctx, subcommand=None, subject=None,
                      tier: int = None, *args):
        if subcommand is None:
            await ctx.send(messages.review_format)
        else:
            guild = self.bot.get_guild(config.guild_id)
            member = guild.get_member(ctx.message.author.id)
            if member == None:
                await ctx.send(messages.review_not_on_server.fromat(user=ctx.message.author.mention))
                return
            roles = member.roles
            if subcommand == 'add':
                for role in roles:
                    if role.id in config.reviews_forbidden_roles:
                        await ctx.send(messages.review_add_denied.format(
                                    user=ctx.message.author.mention))
                        return
                if subject is None or tier is None:
                    await ctx.send(messages.review_add_format)
                    return
                author = ctx.message.author.id
                anonym = False
                if tier < 0 or tier > 4:
                    await ctx.send(messages.review_tier)
                    return
                if not ctx.guild: # DM
                    anonym = True
                if args:
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
    async def subject(self, ctx, subcommand=None, *subjects):
        if ctx.author.id == config.admin_id:
            if not subcommand or not subjects:
                await ctx.send(messages.subject_format)
                return
            if subcommand == "add":
                for subject in subjects:
                    self.rev.add_subject(subject)
                await ctx.send(f'Zkratky `{subjects}` byli přidány')
            elif subcommand == "remove":
                for subject in subjects:
                    self.rev.remove_subject(subject)
                await ctx.send(f'Zkratky `{subjects}` byli odebrány')
            else:
                await ctx.send(messages.review_wrong_subject)
        else:
            await ctx.send(
                messages.insufficient_rights
                .format(user=utils.generate_mention(ctx.author.id)))

class Review_helper():

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def make_embed(self, review, subject, tier_average, page):
        embed = discord.Embed(
            title=subject.lower() + " reviews",
            description="Average tier: " + tier_average
        )
        colour = 0x6d6a69
        id = 0
        if review is not None:
            guild = self.bot.get_guild(config.guild_id)
            if review.anonym:
                author = "Anonym"
            else:
                author = guild.get_member(int(review.member_ID))
            embed.add_field(name="Author", value=author)
            embed.add_field(name="Tier", value=review.tier)
            embed.add_field(name="Date", value=review.date)
            text = review.text_review
            if text is not None:
                text_len = len(text)
                if text_len > 1024:
                    pages = text_len // 1024 + (text_len % 1024 > 0)
                    text = review.text_review[:1024]
                    embed.add_field(name="Text page",
                                    value="1/" + str(pages), inline=False)
                embed.add_field(name="Text", value=text, inline=False)
            likes = review_repo.get_votes_count(review.id, True)
            embed.add_field(name="Likes", value="👍" + str(likes))
            dislikes = review_repo.get_votes_count(review.id, False)
            embed.add_field(name="Dislikes", value="👎" + str(dislikes))
            diff = likes - dislikes
            if diff > 0:
                colour = 0x34cb0b
            elif diff < 0:
                colour = 0xcb410b
            id = review.id
        embed.set_footer(text="Review: " + page + ' | ID: ' + str(id) +
                         " | Last edited at: " +
                         str(datetime.now().replace(microsecond=0)))
        embed.colour = colour
        return embed

    def change_text_page(self, review, embed, new_page, max_page):
        text_index = 1024*(new_page-1)
        if len(review.text_review) < 1024*new_page:
            text = review.text_review[text_index:]
        else:
            text = review.text_review[text_index:1024*new_page]
        embed.set_field_at(
            3, name="Text page", value=str(new_page) + "/" + str(max_page))
        embed.set_field_at(4, name="Text", value=text)
        return embed

    def add_review(self, author_id, subject, tier, anonym, text):
        update = review_repo.get_review_by_author_subject(author_id, subject)
        if update:
            review_repo.update_review(update.id, tier, anonym, text)
        else:
            review_repo.add_review(author_id, subject.lower(), tier, anonym, text)

    def list_reviews(self, subject):
        result = review_repo.get_subject(subject).first()
        if not result:
            return None
        reviews = review_repo.get_subject_reviews(subject)
        tier_cnt = 0
        tier_sum = 0
        for review in reviews:
            tier_sum += review.Review.tier
            tier_cnt += 1
        if tier_cnt == 0:
            tier_average = "No reviews"
            review = None
            page = "1/1"
        else:
            tier_average = str(round(tier_sum/tier_cnt))
            review = reviews[0].Review
            page = "1/" + str(tier_cnt)
        return self.make_embed(review, subject, tier_average, page)

    def remove(self, author, subject):
        result = review_repo.get_review_by_author_subject(author, subject)
        if result:
            review_repo.remove(result.id)
            return True
        else:
            return False

    def add_vote(self, review_id, vote: bool, author):
        relevance = review_repo.get_vote_by_author(review_id, author)
        if not relevance or relevance.vote != vote:
            review_repo.add_vote(review_id, vote, author)

    def add_subject(self, subject):
        review_repo.add_subject(subject)

    def remove_subject(self, subject):
        review_repo.get_subject(subject).delete()


def setup(bot):
    bot.add_cog(Review(bot))
