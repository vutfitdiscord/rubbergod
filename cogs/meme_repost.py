import discord
from discord.ext import commands
from features.reaction_context import ReactionContext
from config.app_config import Config
from repository.karma_repo import KarmaRepository
from repository.meme_repost_repo import MemeRepostRepo
from typing import List, Union
import utils
import asyncio


class MemeRepost(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

        self.karma_repo = KarmaRepository()
        self.repost_repo = MemeRepostRepo()
        self.repost_channel: Union[discord.TextChannel, None] = None

        self.repost_lock = asyncio.Lock()

    async def handle_reaction(self, ctx: ReactionContext):
        # Message was reposted before
        if self.repost_repo.find_repost_by_id(ctx.message.id) is not None:
            return

        all_reactions: List[discord.Reaction] = ctx.message.reactions
        for reac in all_reactions:
            if reac.count >= Config.repost_threshold:
                emoji_key = str(reac.emoji.id) if type(reac.emoji) != str else reac.emoji
                emoji_val = self.karma_repo.emoji_value(emoji_key)

                if int(emoji_val) >= 1:
                    return await self.__repost_message(ctx)

    async def __repost_message(self, ctx: ReactionContext):
        if self.repost_channel is None and Config.meme_repost_room != 0:
            self.repost_channel = await self.bot.fetch_channel(Config.meme_repost_room)

        # Invalid ID
        if self.repost_channel is None:
            return

        async with self.repost_lock:
            if self.repost_repo.find_repost_by_id(ctx.message.id) is not None:
                return

            files = []
            for attachement in ctx.message.attachments:
                file = await attachement.to_file()
                if file is not None:
                    files.append(file)

            number_of_files = len(files)

            embed = discord.Embed(color=discord.Color.dark_blue())
            utils.add_author_footer(embed, author=ctx.message.author)

            link = utils.fill_message("meme_repost_link",
                                      original_message_url=ctx.message.jump_url,
                                      original_channel=Config.meme_room)
            embed.add_field(name="Link", value=link, inline=False)

            if ctx.message.content:
                embed.add_field(name="Obsah", value=ctx.message.content[:1023])

            if number_of_files > 0:
                embed.set_image(url=f"attachment://{files[0].filename}")

            main_file = files[0] if number_of_files > 0 else None
            repost_message = await self.repost_channel.send(embed=embed, file=main_file)

            sec_repost_message_id = None
            if number_of_files > 1:
                sec_message = await self.repost_channel.send(files=files[1:11])
                sec_repost_message_id = sec_message.id

            self.repost_repo.create_repost(ctx.message.id, repost_message.id, ctx.member.id,
                                           sec_repost_message_id)


def setup(bot):
    bot.add_cog(MemeRepost(bot))
