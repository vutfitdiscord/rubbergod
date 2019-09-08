import discord
from discord.ext import commands
from discord.ext.commands import Bot

from features.base_feature import BaseFeature
from repository import review_repo
from config import config, messages

review_r = review_repo.ReviewRepository()
config = config.Config

class Review(BaseFeature):

    def __init__(self, bot: Bot):
        super().__init__(bot)

    def add_review(self, author_id, subject, tier, anonym, text):
        update = review_r.get_review_by_author_subject(author_id, subject)
        if update:
            review_r.update_review(update.id, tier, anonym, text)
        else:
            review_r.add_review(author_id, subject.lower(), tier, anonym, text)

    def list_reviews(self, subject):
        reviews = review_r.get_subject_reviews(subject)
        embed = discord.Embed(title=subject.upper() + " reviews",
                    color=0xeee657)
        guild = self.bot.get_guild(config.guild_id)
        for review in reviews:
            if review.anonym == True:
                author = "Anonym"
            else:
                author = guild.get_member(int(review.member_ID))
            embed.add_field(name="Autor", value=author, inline=True)
            embed.add_field(name="Tier", value=review.tier)
            if review.text_review is not None:
                embed.add_field(name="Text", value=review.text_review, inline=False)
        return embed
