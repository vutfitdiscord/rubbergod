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
        if self.repost_repo.find_repost_by_original_message_id(ctx.message.id) is not None:
            return

        all_reactions: List[discord.Reaction] = ctx.message.reactions
        for reac in all_reactions:
            if reac.count >= Config.repost_threshold:
                emoji_key = str(reac.emoji.id) if type(reac.emoji) != str else reac.emoji
                emoji_val = self.karma_repo.emoji_value(emoji_key)

                if int(emoji_val) >= 1:
                    return await self.__repost_message(ctx, all_reactions)

    async def __repost_message(self, ctx: ReactionContext,
                               reactions: List[discord.Reaction]):
        if self.repost_channel is None and Config.meme_repost_room != 0:
            self.repost_channel = await self.bot.fetch_channel(Config.meme_repost_room)

        # Invalid ID
        if self.repost_channel is None:
            return

        async with self.repost_lock:
            if self.repost_repo.find_repost_by_original_message_id(ctx.message.id) is not None:
                return

            # Generate string with all reactions on post at the time
            title_string = ""
            for reaction in reactions:
                tmp_string = title_string + f"{reaction.count}x{reaction.emoji} "

                if len(tmp_string) >= 255:
                    break

                title_string = tmp_string

            embed = discord.Embed(color=discord.Color.dark_blue(), title=title_string)
            utils.add_author_footer(embed, author=ctx.message.author)

            # Create link to original post
            link = utils.fill_message("meme_repost_link",
                                      original_message_url=ctx.message.jump_url,
                                      original_channel=Config.meme_room)
            embed.add_field(name="Link", value=link, inline=False)

            # Get all attachements of original post
            main_image = None
            more_images = False
            attachement_urls = []
            for attachement in ctx.message.attachments:
                if attachement.content_type.split("/")[0] == "image":
                    if main_image is None:
                        main_image = await attachement.to_file()
                    else:
                        more_images = True
                else:
                    attachement_urls.append(attachement.proxy_url)

            # Set content from original message if present
            if ctx.message.content:
                content = ctx.message.content[:900]
                if more_images:
                    content += "\n\nVíce obrázků v původním postu"
                embed.add_field(name="Obsah", value=content)
            elif more_images:
                embed.add_field(name="Obsah", value="Více obrázků v původním postu")

            # Set main image if present
            if main_image is not None:
                embed.set_image(url=f"attachment://{main_image.filename}")

            # Add all attachements as fields
            for idx, attachement_url in enumerate(attachement_urls):
                embed.add_field(name=f"Příloha {idx + 1}", value=attachement_url, inline=False)

            repost_message = await self.repost_channel.send(embed=embed, file=main_image)

            self.repost_repo.create_repost(ctx.message.id, repost_message.id, ctx.member.id)


def setup(bot):
    bot.add_cog(MemeRepost(bot))
