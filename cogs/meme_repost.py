import asyncio
from typing import List, Union

import disnake
from disnake.ext import commands

import utils
from config.app_config import config
from features.reaction_context import ReactionContext
from repository.karma_repo import KarmaRepository
from repository.meme_repost_repo import MemeRepostRepo


class MemeRepost(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

        self.karma_repo = KarmaRepository()
        self.repost_repo = MemeRepostRepo()
        self.repost_channel: Union[disnake.TextChannel, None] = None

        self.repost_lock = asyncio.Lock()

    async def handle_reaction(self, ctx: ReactionContext):
        if ctx.channel.id == config.meme_room:
            if self.repost_repo.find_repost_by_original_message_id(ctx.message.id) is not None:
                # Message was reposted before
                return

            all_reactions: List[disnake.Reaction] = ctx.message.reactions
            for reac in all_reactions:
                if reac.count >= config.repost_threshold:
                    emoji_key = str(reac.emoji.id) if type(reac.emoji) != str else reac.emoji
                    emoji_val = self.karma_repo.emoji_value(emoji_key)

                    if int(emoji_val) >= 1:
                        return await self.__repost_message(ctx, all_reactions)
        elif ctx.channel.id == config.meme_repost_room:
            repost = self.repost_repo.find_repost_by_repost_message_id(ctx.message.id)

            if repost is not None:
                if ctx.member.id == int(repost.author_id):
                    return

                original_post_user = ctx.guild.get_member(int(repost.author_id))

                if original_post_user:
                    if isinstance(ctx.emoji, str):
                        self.karma_repo.karma_emoji(original_post_user.id, ctx.member.id, ctx.emoji)
                    else:
                        self.karma_repo.karma_emoji(original_post_user.id, ctx.member.id, ctx.emoji.id)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        ctx: ReactionContext = await ReactionContext.from_payload(self.bot, payload)
        if ctx is None:
            return

        if ctx.channel.id != config.meme_repost_room:
            return

        repost = self.repost_repo.find_repost_by_repost_message_id(ctx.message.id)
        if repost is not None:

            if ctx.member.id == int(repost.author_id):
                return

            original_post_user = ctx.guild.get_member(int(repost.author_id))

            if original_post_user:
                if isinstance(ctx.emoji, str):
                    self.karma_repo.karma_emoji_remove(original_post_user.id, ctx.member.id, ctx.emoji)
                else:
                    self.karma_repo.karma_emoji_remove(original_post_user.id, ctx.member.id, ctx.emoji.id)

    async def __repost_message(self, ctx: ReactionContext,
                               reactions: List[disnake.Reaction]):
        if self.repost_channel is None and config.meme_repost_room != 0:
            self.repost_channel = await self.bot.fetch_channel(config.meme_repost_room)

        # Invalid ID
        if self.repost_channel is None:
            return

        async with self.repost_lock:
            if self.repost_repo.find_repost_by_original_message_id(ctx.message.id) is not None:
                return

            # Generate string with all reactions on post at the time
            title_string = ""
            for reaction in reactions:
                if not isinstance(reaction.emoji, str):
                    # Remove all emoji reactions that are not from current server
                    if disnake.utils.get(ctx.guild.emojis, id=reaction.emoji.id) is None:
                        continue

                tmp_string = title_string + f"{reaction.count}x{reaction.emoji} "

                if len(tmp_string) >= 255:
                    break

                title_string = tmp_string

            embed = disnake.Embed(color=disnake.Color.dark_blue(), title=title_string)
            utils.add_author_footer(embed, author=ctx.message.author)
            embed.timestamp = ctx.message.created_at

            # Create link to original post
            link = utils.fill_message("meme_repost_link",
                                      original_message_url=ctx.message.jump_url,
                                      original_channel=config.meme_room)
            embed.add_field(name="Link", value=link, inline=False)

            # Get all attachments of original post
            main_image = None
            other_attachments = []
            for attachment in ctx.message.attachments:
                content_type = attachment.content_type
                if content_type is not None and content_type.split("/")[0] == "image" and main_image is None:
                    # Set main image if its image and main image is not set
                    main_image = await attachment.to_file()
                else:
                    # Other attachments convert to file and append to list of attachments
                    attachment_file = await attachment.to_file()
                    if attachment_file is not None:
                        other_attachments.append(attachment_file)

            # Set content from original message if present
            if ctx.message.content:
                content_splits = ctx.message.content.split()
                for content_split in content_splits:
                    if content_split.startswith("https://"):
                        # Its attachement URL
                        for extension in config.meme_repost_image_extensions:
                            # Check for extension in URL
                            if f".{extension}" in content_split:
                                if main_image is None:
                                    main_image = content_split
                                else:
                                    other_attachments.append(content_split)
                                break
                        else:
                            other_attachments.append(content_split)

                content = ctx.message.content[:900]
                embed.add_field(name="Obsah", value=content)

            # Set main image if present
            if main_image is not None:
                if isinstance(main_image, disnake.File):
                    embed.set_image(url=f"attachment://{main_image.filename}")
                elif isinstance(main_image, str):
                    embed.set_image(url=main_image)
                    main_image = None
                else:
                    main_image = None

            repost_message_id = -1
            secondary_message_id = None
            if len(embed) < 6000:
                repost_message = await self.repost_channel.send(embed=embed, file=main_image)
                repost_message_id = repost_message.id

                if len(other_attachments) > 0:
                    # Files are getting send as files
                    files = [file for file in other_attachments if isinstance(file, disnake.File)]
                    files = files[:10] if files else None

                    # And urls as string in separated message
                    urls = [file for file in other_attachments if isinstance(file, str)]
                    urls = "\n".join(urls) if urls else None

                    secondary_message = await self.repost_channel.send(urls, files=files)
                    secondary_message_id = secondary_message.id

            self.repost_repo.create_repost(ctx.message.id,
                                           repost_message_id,
                                           ctx.message.author.id,
                                           secondary_message_id)


def setup(bot):
    bot.add_cog(MemeRepost(bot))
