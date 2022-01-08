import discord
from discord.ext import commands
from features.reaction_context import ReactionContext
from config.app_config import Config
from repository.karma_repo import KarmaRepository
from repository.meme_repost_repo import MemeRepostRepo
from typing import List, Union
import utils


class MemeRepost(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

        self.karma_repo = KarmaRepository()
        self.repost_repo = MemeRepostRepo()
        self.repost_channel: Union[discord.TextChannel, None] = None

    async def handle_reaction(self, ctx: ReactionContext):
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

        number_of_files = len(files)

        embed = discord.Embed(description=ctx.message.content, color=discord.Color.dark_blue())
        utils.add_author_footer(embed, author=ctx.message.author)

        if number_of_files > 0:
            embed.set_image(url=f"attachment://{files[0].filename}")

        repost_message = await self.repost_channel.send(embed=embed,
                                                        file=files[0] if number_of_files > 0 else None)

        sec_repost_message_id = None
        if number_of_files > 1:
            sec_repost_message_id = await self.repost_channel.send(files=files[1:11])

        self.repost_repo.create_repost(ctx.message.id, repost_message.id, ctx.member.id,
                                       sec_repost_message_id)


def setup(bot):
    bot.add_cog(MemeRepost(bot))
