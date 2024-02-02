from __future__ import annotations

import re
from collections import Counter
from typing import List

import disnake

import utils
from config.messages import Messages


class Image:
    def __init__(self, message_url: str, emojis: list[Emoji], invalid_votes: int = 0):
        self.message_url: str = message_url
        self.emojis: list[Emoji] = emojis
        self.invalid_votes: int = invalid_votes

    @property
    def total_value(self):
        total = 0
        for emoji in self.emojis:
            total += emoji.total_value
        return total


class Emoji:
    def __init__(self, emoji: str, count: int, value: float):
        self.emoji: str = emoji
        self.count: int = count
        self.value: float = value

    @property
    def total_value(self):
        return float(self.count * self.value)


def get_contribution_id(content: str) -> int:
    """extracts the contribution id from the string"""
    contribution_id = re.match(r".*ID: (\d+).*", content).group(1)
    return int(contribution_id)


async def get_top_contributions(self, messages: list[disnake.Message], number_of: int) -> List[str]:
    images = []

    # get all images and their votes
    for message in messages:
        # skip messages without reactions
        if not message.reactions:
            continue

        # Create an empty list to store Emoji objects for this message
        emojis_for_message = []

        # Create a dictionary to store all reactions for this message only once
        reactions_list = {}
        duplicate_votes = Counter()
        for r in message.reactions:
            reactions_list[r] = {user.id for user in await r.users().flatten()}
            duplicate_votes.update(user for user in reactions_list[r])
        duplicate_votes = {user for user, count in duplicate_votes.items() if count > 1}

        # iterate reactions and create Emoji objects for each reaction
        for r, users in reactions_list.items():
            users = users - duplicate_votes
            emoji = utils.str_emoji_id(r.emoji)
            if emoji in self.emojis:
                emoji_obj = Emoji(emoji=emoji, count=len(users), value=self.emojis[emoji])
                emojis_for_message.append(emoji_obj)
        images.append(Image(message.jump_url, emojis_for_message, len(duplicate_votes)-1))  # -1 for the bot

    messages = []
    # Sort the images by total_value in descending order and get the top n
    sorted_images = sorted(images, key=lambda x: x.total_value, reverse=True)[:number_of]

    emoji_string = "- {emoji.emoji}: Count: {emoji.count} - Total: {emoji.total_value}\n"
    # calculate values for each image
    for image in sorted_images:
        if image.total_value == 0:
            continue
        emoji_strings = [emoji_string.format(emoji=emoji) for emoji in image.emojis]
        content = f"{image.message_url} - Total: **{image.total_value}**\n{''.join(emoji_strings)}\n"
        if image.invalid_votes > 0:
            content += Messages.contest_vote_invalid_votes(invalid_votes=image.invalid_votes)

        messages.append(content)
    return messages
