import discord
from discord.ext import commands
import sqlalchemy

from features.reaction_context import ReactionContext
from config.app_config import Config
from utils import is_command_message
from repository.database import session


class Reaction(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Catch reaction, get all properties and then call proper cog/s"""
        ctx: ReactionContext = await ReactionContext.from_payload(self.bot, payload)
        if ctx is None:
            return

        if self.bot.get_cog("Vote") is not None and (is_command_message('vote', ctx.message.content)
                or is_command_message('singlevote', ctx.message.content, False)):
            try:
                await self.bot.get_cog("Vote").handle_raw_reaction_add(payload)
            except sqlalchemy.exc.InternalError:
                session.rollback()
            return

        cogs = []

        if (
            ctx.message.embeds
            and ctx.message.embeds[0].title is not discord.Embed.Empty
            and "reviews" in ctx.message.embeds[0].title
        ):
            cogs.append(self.bot.get_cog("Review"))
        if ctx.emoji == "📌":
            cogs.append(self.bot.get_cog("AutoPin"))
        if ctx.channel.id not in Config.role_channels:
            cogs.append(self.bot.get_cog("Karma"))
        else:
            cogs.append(self.bot.get_cog("ReactToRole"))
        if (
            ctx.emoji == "❎"
            and payload.channel_id in Config.deduplication_channels
            and not payload.member.bot
            and ctx.message.author.bot
        ):
            cogs.append(self.bot.get_cog("Warden"))
        if(
            ctx.message.embeds
            and ctx.message.embeds[0].author.name is not discord.Embed.Empty
            and "streamlinks" in ctx.message.embeds[0].author.name.lower()
        ):
            cogs.append(self.bot.get_cog("StreamLinks"))

        if ctx.channel.id == Config.meme_room:
            cogs.append(self.bot.get_cog("MemeRepost"))

        for cog in cogs:
            # check if cog is loaded
            if cog:
                try:
                    await cog.handle_reaction(ctx)
                except sqlalchemy.exc.InternalError:
                    session.rollback()


def setup(bot):
    bot.add_cog(Reaction(bot))
