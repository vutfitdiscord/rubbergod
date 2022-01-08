import discord
from discord.ext import commands
from features.reaction_context import ReactionContext
from config.app_config import Config
from repository.karma_repo import KarmaRepository
from repository.meme_repost_repo import MemeRepostRepo
from typing import List, Union


class MemeRepost(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

        self.karma_repo = KarmaRepository()
        self.repost_repo = MemeRepostRepo()
        self.repost_channel:Union[discord.TextChannel, None] = None

    async def handle_reaction(self, ctx:ReactionContext):
        if ctx.channel.id != Config.meme_room:
            return

        # Message was reposted before
        if self.repost_repo.find_repost_by_id(ctx.message.id) is not None:
            return

        all_reactions: List[discord.Reaction] = ctx.message.reactions
        for reaction in all_reactions:
            if reaction.count >= Config.repost_threshold:
                if int(self.karma_repo.emoji_value(str(reaction.emoji.id) if
                        type(reaction.emoji) != str else reaction.emoji)) > Config.repost_threshold:
                    return await self.__repost_message(ctx)

    async def __repost_message(self, ctx: ReactionContext):
        if self.repost_channel is None and Config.meme_repost_room != 0:
            self.repost_channel = await self.bot.fetch_channel(Config.meme_repost_room)

        # Invalid ID
        if self.repost_channel is None:
            return

        files = []
        for attachement in ctx.message.attachments:
            file = await attachement.to_file()
            if file is not None:
                files.append(file)

        # TODO: Think about more clever way of reposting messages
        repost_message = await self.repost_channel.send(ctx.message.content, files=files[:10])

        self.repost_repo.create_repost(ctx.message.id, repost_message.id, ctx.member.id)

def setup(bot):
    bot.add_cog(MemeRepost(bot))
