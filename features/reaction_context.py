import discord
from discord.ext.commands import Bot
from typing import Union
from config.app_config import config


class ReactionContext():
    channel: discord.TextChannel
    guild: discord.Guild
    member: discord.Member
    message: discord.Message
    reply_to: discord.Message
    emoji: Union[discord.Emoji, str]

    def __init__(self, channel, guild, member, message, reply_to, emoji):
        self.channel = channel
        self.guild = guild
        self.member = member
        self.message = message
        self.reply_to = reply_to
        self.emoji = emoji

    @staticmethod
    async def from_payload(bot: Bot, payload: discord.RawReactionActionEvent):
        channel: discord.TextChannel = bot.get_channel(payload.channel_id)
        if channel is None:
            return None

        if channel.type is discord.ChannelType.text:
            guild = channel.guild
        else:
            guild = bot.get_guild(config.guild_id)
            if guild is None:
                raise Exception("Nemůžu najít guildu podle config.guild_id")

        member = payload.member if payload.member is not None else guild.get_member(payload.user_id)
        if member is None or member.bot:
            return None

        try:
            message: discord.Message = await channel.fetch_message(payload.message_id)

            if message is None:
                return None
        except discord.errors.NotFound:
            return None

        reply_to = None
        if message is not None and message.reference is not None and message.reference.message_id is not None:
            try:
                reply_to = await channel.fetch_message(message.reference.message_id)
            except discord.errors.NotFound:
                pass  # Reply is there optional.

        if payload.emoji.is_custom_emoji():
            emoji = bot.get_emoji(payload.emoji.id)
            if emoji is None:
                emoji = payload.emoji
        else:
            emoji = payload.emoji.name

        return ReactionContext(channel, guild, member, message, reply_to, emoji)
