"""
Cog for handling reactions and delegating to specific cog.
"""

import disnake
import sqlalchemy
from disnake.ext import commands

from cogs.base import Base
from database import session
from features.reaction_context import ReactionContext
from rubbergod import Rubbergod


class Reactions(Base, commands.Cog):
    def __init__(self, bot: Rubbergod):
        super().__init__()
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: disnake.RawReactionActionEvent):
        """Catch reaction, get all properties and then call proper cog/s"""
        ctx = await ReactionContext.from_payload(self.bot, payload)
        if ctx is None:
            return

        cogs = []
        # send embed to user where he left reading
        if ctx.emoji == "🔖":
            try:
                await self.bot.get_cog("Bookmark").bookmark_reaction(ctx)
            except AttributeError:
                pass  # cog not loaded
            return

        if ctx.emoji == "📌":
            cogs.append(self.bot.get_cog("AutoPin"))
        if ctx.channel.id == self.config.contest_vote_channel:
            cogs.append(self.bot.get_cog("ContestVote"))
        if ctx.channel.id not in self.config.role_channels:
            cogs.append(self.bot.get_cog("Karma"))
        else:
            cogs.append(self.bot.get_cog("Roles"))
        if (
            ctx.emoji == "❎"
            and payload.channel_id in self.config.deduplication_channels
            and not payload.member.bot
            and ctx.message.author.bot
        ):
            cogs.append(self.bot.get_cog("Warden"))

        if (
            ctx.channel.id == self.config.meme_room or ctx.channel.id == self.config.bettermeme_room
        ) and ctx.message.author.id != ctx.member.id:
            cogs.append(self.bot.get_cog("BetterMeme"))

        if ctx.emoji == "🔇":
            cogs.append(self.bot.get_cog("TimeoutWars"))

        for cog in cogs:
            # check if cog is loaded
            if cog:
                try:
                    await cog.handle_reaction(ctx)
                except sqlalchemy.exc.InternalError:
                    session.rollback()
                except disnake.errors.DiscordServerError:
                    pass
