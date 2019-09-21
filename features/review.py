import discord
from discord.ext.commands import Bot

from features.base_feature import BaseFeature
from repository import review_repo
from config import config

review_r = review_repo.ReviewRepository()
config = config.Config


class Review(BaseFeature):

    def __init__(self, bot: Bot):
        super().__init__(bot)

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
            likes = review_r.get_votes_count(review.id, True)
            embed.add_field(name="Likes", value="👍" + str(likes))
            dislikes = review_r.get_votes_count(review.id, False)
            embed.add_field(name="Dislikes", value="👎" + str(dislikes))
            diff = likes - dislikes
            if diff > 0:
                colour = 0x34cb0b
            elif diff < 0:
                colour = 0xcb410b
            id = review.id
        embed.set_footer(text="Review: " + page + ' | ID: ' + str(id))
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
        update = review_r.get_review_by_author_subject(author_id, subject)
        if update:
            review_r.update_review(update.id, tier, anonym, text)
        else:
            review_r.add_review(author_id, subject.lower(), tier, anonym, text)

    def list_reviews(self, subject):
        result = review_r.get_subject(subject).first()
        if not result:
            return None
        reviews = review_r.get_subject_reviews(subject)
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
        result = review_r.get_review_by_author_subject(author, subject)
        if result:
            review_r.remove(result.id)
            return True
        else:
            return False

    def add_vote(self, review_id, vote: bool, author):
        relevance = review_r.get_vote_by_author(review_id, author)
        if not relevance or relevance.vote != vote:
            review_r.add_vote(review_id, vote, author)

    def add_subject(self, subject):
        review_r.add_subject(subject)

    def remove_subject(self, subject):
        review_r.get_subject(subject).delete()
