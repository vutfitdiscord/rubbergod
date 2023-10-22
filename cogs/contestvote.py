"""
Cog for handling vote reactions for contests.
"""
from __future__ import annotations

from functools import cached_property

import disnake
from disnake.ext import commands

from cogs.base import Base
from config import cooldowns
from config.messages import Messages
from features.reaction_context import ReactionContext
from utils import str_emoji_id


class Image:
    def __init__(self, message_url: str, emojis: list[Emoji]):
        self.message_url: str = message_url
        self.emojis: list[Emoji] = emojis

    @property
    def total_value(self):
        total = 0
        for emoji in self.emojis:
            total += emoji.total_value
        return total


class Emoji:
    def __init__(self, emoji: str, count: int, value: int):
        self.emoji: str = emoji
        self.count: int = count
        self.value: int = value

    @property
    def total_value(self):
        return self.count * self.value


class ContestVote(Base, commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

        self.emojis = {
            str("1️⃣"): self.config.contest_vote_weight_1,
            str("2️⃣"): self.config.contest_vote_weight_2,
            str("3️⃣"): self.config.contest_vote_weight_3
        }

    @cached_property
    def contest_room(self) -> disnake.TextChannel:
        return self.bot.get_channel(self.config.contest_vote_channel)

    @cooldowns.default_cooldown
    @commands.slash_command(name="contest",)
    async def contest(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()

    @contest.sub_command(name="calculate_message", description=Messages.contest_vote_calculate_message_brief)
    async def calculate_image(self, inter: disnake.ApplicationCommandInteraction, message_url: str):
        try:
            message: disnake.Message = await commands.MessageConverter().convert(inter, message_url)
        except commands.MessageNotFound:
            await inter.send(Messages.message_not_found)
            return

        if not message.reactions:
            await inter.send(Messages.contest_vote_no_reactions)
            return

        # Create an empty list to store Emoji objects for this message
        emojis_for_message = []

        for r in message.reactions:
            emoji = str_emoji_id(r.emoji)
            if emoji in self.emojis:
                emoji_obj = Emoji(emoji=emoji, count=r.count - 1, value=self.emojis[emoji])
                emojis_for_message.append(emoji_obj)
        image = Image(message.jump_url, emojis_for_message)

        # calculate values
        if image.total_value == 0:
            await inter.send(Messages.contest_vote_no_votes)
            return
        emoji_strings = [f"- {emoji.emoji}: Count: {emoji.count} - Total: {emoji.total_value}\n"
                         for emoji in image.emojis]
        message = f"{image.message_url} - Total: **{image.total_value}**\n{''.join(emoji_strings)}"

        await inter.send(message)

    @contest.sub_command(name="winners", description=Messages.contest_vote_winners_brief)
    async def winners(self, inter: disnake.ApplicationCommandInteraction):
        messages = await self.contest_room.history().flatten()
        images = []

        # get all images and their votes
        for message in messages:
            # skip messages without reactions
            if not message.reactions:
                continue

            # Create an empty list to store Emoji objects for this message
            emojis_for_message = []

            # iterate reactions and create Emoji objects for each reaction
            for r in message.reactions:
                emoji = str_emoji_id(r.emoji)
                if emoji in self.emojis:
                    emoji_obj = Emoji(emoji=emoji, count=r.count - 1, value=self.emojis[emoji])
                    emojis_for_message.append(emoji_obj)
            images.append(Image(message.jump_url, emojis_for_message))

        messages = []
        # Sort the images by total_value in descending order and get the top 5
        sorted_images = sorted(images, key=lambda x: x.total_value, reverse=True)[:5]

        # calculate values for each image
        for image in sorted_images:
            if image.total_value == 0:
                continue
            emoji_strings = [f"- {emoji.emoji}: Count: {emoji.count} - Total: {emoji.total_value}\n"
                             for emoji in image.emojis]
            messages.append(f"{image.message_url} - Total: **{image.total_value}**\n{''.join(emoji_strings)}")

        await inter.send("".join(messages))

    def is_contest_room(self, ctx):
        return ctx.channel.id == self.config.contest_vote_channel

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        """Add reactions to contest vote messages"""
        if not self.is_contest_room(message):
            return

        for emoji in self.emojis:
            await message.add_reaction(emoji)

    @commands.check(is_contest_room)
    async def handle_reaction(self, ctx: ReactionContext):
        """Allow only one reaction per user"""
        if ctx is None:
            return

        emoji_str = str_emoji_id(ctx.emoji)
        message = await ctx.channel.fetch_message(ctx.message.id)
        user = await self.bot.get_or_fetch_user(ctx.member.id)
        for r in message.reactions:
            if str_emoji_id(r.emoji) == emoji_str:
                continue
            if await r.users().find(lambda x: x.id == user.id):
                await message.remove_reaction(ctx.emoji, user)
                return


def setup(bot):
    bot.add_cog(ContestVote(bot))
