"""
Cog for handling memes with X number of reactions to be reposted to a specific channel.
"""

import asyncio
from functools import cached_property
from typing import List

import disnake
from disnake.ext import commands

import utils
from buttons.embed import EmbedView
from cogs.base import Base
from config.messages import Messages
from database.better_meme import BetterMemeDB
from database.karma import KarmaDB, KarmaEmojiDB
from database.meme_repost import MemeRepostDB
from features.leaderboard import LeaderboardPageSource
from features.reaction_context import ReactionContext
from permissions import room_check


def _leaderboard_formatter(entry: BetterMemeDB, **kwargs):
    return Messages.base_leaderboard_format_str.format_map(
        kwargs) + f" **{entry.posts}** posts **{entry.total_karma}** pts"


class MemeRepost(Base, commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot: commands.Bot = bot

        self.better_db = BetterMemeDB()
        self.check = room_check.RoomCheck(bot)

        self.repost_lock = asyncio.Lock()

    @cached_property
    def repost_channel(self):
        return self.bot.get_channel(self.config.meme_repost_room)

    async def handle_reaction(self, ctx: ReactionContext):
        if ctx.channel.id == self.config.meme_room:
            if MemeRepostDB.find_repost_by_original_message_id(ctx.message.id) is not None:
                # Message was reposted before
                return

            all_reactions: List[disnake.Reaction] = ctx.message.reactions
            for reac in all_reactions:
                if reac.count >= self.config.repost_threshold:
                    emoji_key = str(reac.emoji.id) if type(reac.emoji) != str else reac.emoji
                    emoji_val = KarmaEmojiDB.emoji_value(emoji_key)

                    if int(emoji_val) >= 1:
                        await self.__repost_message(ctx, all_reactions)
                        return
        elif ctx.channel.id == self.config.meme_repost_room:
            repost = MemeRepostDB.find_repost_by_repost_message_id(ctx.message.id)

            if repost is not None:
                if ctx.member.id == int(repost.author_id):
                    return

                original_post_user = ctx.guild.get_member(int(repost.author_id))

                if original_post_user:
                    emoji_key = utils.str_emoji_id(ctx.emoji)
                    emoji_val = KarmaEmojiDB.emoji_value(emoji_key)
                    BetterMemeDB.update_post_karma(original_post_user.id, emoji_val)
                    KarmaDB.karma_emoji(original_post_user.id, ctx.member.id, emoji_key)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        ctx: ReactionContext = await ReactionContext.from_payload(self.bot, payload)
        if ctx is None:
            return

        if ctx.channel.id != self.config.meme_repost_room:
            return

        repost = MemeRepostDB.find_repost_by_repost_message_id(ctx.message.id)
        if repost is not None:

            if ctx.member.id == int(repost.author_id):
                return

            original_post_user = ctx.guild.get_member(int(repost.author_id))

            if original_post_user:
                emoji_key = utils.str_emoji_id(ctx.emoji)
                emoji_val = KarmaEmojiDB.emoji_value(emoji_key)
                BetterMemeDB.update_post_karma(original_post_user.id, -emoji_val)
                KarmaDB.karma_emoji_remove(original_post_user.id, ctx.member.id, emoji_key)

    async def __repost_message(self, ctx: ReactionContext,
                               reactions: List[disnake.Reaction]):
        # Invalid ID
        if self.repost_channel is None:
            return
        async with self.repost_lock:
            if MemeRepostDB.find_repost_by_original_message_id(ctx.message.id) is not None:
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
            link = Messages.meme_repost_link(original_message_url=ctx.message.jump_url,
                                             original_channel=self.config.meme_room)
            embed.add_field(name="Link", value=link, inline=False)

            # Get all attachments of original post
            main_image = None
            other_attachments = []
            for attachment in ctx.message.attachments:
                content_type = attachment.content_type
                if content_type is not None and content_type.split("/")[0] == "image" and main_image is None:
                    # Set main image if its image and main image is not set
                    if attachment.is_spoiler():
                        # if image has spoiler it must be in other_attachments
                        # because embeds don't support images with spoiler
                        attachment_file = await attachment.to_file()
                        other_attachments.append(attachment_file)
                    else:
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
                        for extension in self.config.meme_repost_image_extensions:
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

            MemeRepostDB.create_repost(
                ctx.message.id,
                repost_message_id,
                ctx.message.author.id,
                secondary_message_id
            )

            total_karma = 0

            for reac in reactions:
                emoji_key = utils.str_emoji_id(reac.emoji)
                emoji_val = KarmaEmojiDB.emoji_value(emoji_key)
                total_karma += reac.count * emoji_val

            BetterMemeDB.add_post_to_repo(ctx.message.author.id, total_karma)

    @commands.slash_command(name="better-meme", guild_ids=[Base.config.guild_id])
    async def _better_meme(self, inter):
        pass

    @_better_meme.sub_command(name="leaderboard", description=Messages.meme_leaderboard_brief)
    async def leaderboard(
        self,
        inter: disnake.ApplicationCommandInteraction,
        order_by: str = commands.Param(name='order_by', choices=["total_karma", "posts"], default="posts"),
        start: int = commands.Param(default=1, gt=0, lt=100000000, description=Messages.karma_board_start)
    ):
        await inter.response.defer(ephemeral=self.check.botroom_check(inter))

        embed = disnake.Embed()
        page_source = LeaderboardPageSource(
            bot=self.bot,
            author=inter.author,
            query=BetterMemeDB.get_leaderboard(order_by),
            row_formatter=_leaderboard_formatter,
            base_embed=embed,
            title='BETTER MEMES LEADERBOARD',
            emote_name='trophy',
            member_id_col_name='member_ID',
        )
        page_num = page_source.get_page_number(start)
        page = page_source.get_page(page_num)
        embed = page_source.format_page(page)

        view = EmbedView(inter.author, embeds=[embed], page_source=page_source)
        await inter.edit_original_response(embed=embed, view=view)
        view.message = await inter.original_message()


def setup(bot):
    bot.add_cog(MemeRepost(bot))
