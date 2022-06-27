import disnake
from disnake.ext import commands
import sqlalchemy

from features.reaction_context import ReactionContext
from config.app_config import config
from utils import is_command_message
from repository.database import session


class Reactions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Catch reaction, get all properties and then call proper cog/s"""
        ctx: ReactionContext = await ReactionContext.from_payload(self.bot, payload)
        if ctx is None:
            return

        if self.bot.get_cog("Vote") is not None and (
            is_command_message("vote", ctx.message.content)
            or is_command_message("singlevote", ctx.message.content, False)
        ):
            try:
                await self.bot.get_cog("Vote").handle_raw_reaction_add(payload)
            except sqlalchemy.exc.InternalError:
                session.rollback()
            return

        cogs = []
        # send embed to user where he left reading
        if ctx.emoji == "🔖":
            await self.bot.get_cog("Bookmark").bookmark_reaction(ctx)
            return

        if ctx.emoji == "📌":
            cogs.append(self.bot.get_cog("AutoPin"))
        if ctx.channel.id not in config.role_channels:
            cogs.append(self.bot.get_cog("Karma"))
        else:
            cogs.append(self.bot.get_cog("Roles"))
        if (
            ctx.emoji == "❎"
            and payload.channel_id in config.deduplication_channels
            and not payload.member.bot
            and ctx.message.author.bot
        ):
            cogs.append(self.bot.get_cog("Warden"))

        if (ctx.channel.id == config.meme_room or ctx.channel.id == config.meme_repost_room) and \
                ctx.message.author.id != ctx.member.id:
            cogs.append(self.bot.get_cog("MemeRepost"))

        for cog in cogs:
            # check if cog is loaded
            if cog:
                try:
                    await cog.handle_reaction(ctx)
                except sqlalchemy.exc.InternalError:
                    session.rollback()
                except disnake.errors.DiscordServerError:
                    pass


def setup(bot):
    bot.add_cog(Reactions(bot))
