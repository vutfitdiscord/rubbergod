"""
Cog implementing karma system. Users can give each other positive/negative karma points with reactions.
"""

import math

import disnake
from disnake.ext import commands, tasks

import utils
from buttons.embed import EmbedView
from cogs.base import Base
from cogs.grillbotapi import GrillbotApi
from config import cooldowns
from config.messages import Messages
from database.karma import KarmaDB
from features import karma
from features.leaderboard import LeaderboardPageSource
from features.reaction_context import ReactionContext
from permissions import permission_check, room_check


class Karma(Base, commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.karma_helper = karma.Karma(bot)
        self.check = room_check.RoomCheck(bot)
        self.grillbot_api = GrillbotApi(bot)
        self._leaderboard_formatter = utils.make_pts_column_row_formatter(KarmaDB.karma.name)
        self._positive_formatter = utils.make_pts_column_row_formatter(KarmaDB.positive.name)
        self._negative_formatter = utils.make_pts_column_row_formatter(KarmaDB.negative.name)
        self.tasks = [self.sync_with_grillbot_task.start()]

    async def handle_reaction(self, ctx: ReactionContext):
        # handle karma vote
        if ctx.message.content.startswith(Messages.karma_vote_message_hack):
            if ctx.emoji not in ["✅", "❌", "0⃣"]:
                await ctx.message.remove_reaction(ctx.emoji, ctx.member)
            else:
                users = []
                for reaction in ctx.message.reactions:
                    users.append(await reaction.users().flatten())
                # Flatten the final list
                users = [x for y in users for x in y]
                if users.count(ctx.member) > 1:
                    await ctx.message.remove_reaction(ctx.emoji, ctx.member)
        # reeval karma message
        elif (
            ctx.message.embeds
            and ctx.message.embeds[0].title is not None
            and ctx.message.embeds[0].title == "Karma zprávy"
            and ctx.emoji == "🔁"
        ):
            async with ctx.channel.typing():
                await ctx.message.remove_reaction(ctx.emoji, ctx.member)
                msg_converter = commands.MessageConverter()
                try:
                    message = await msg_converter.convert(self, ctx.message.embeds[0].fields[0].value)
                except commands.errors.MessageNotFound:
                    ctx.message.delete()
                    return
                embed = await self.karma_helper.message_karma(ctx.member, message)
                await ctx.message.edit(embed=embed)
        # handle karma
        elif (
            ctx.member.id != ctx.message.author.id
            and ctx.guild.id == self.config.guild_id
            and ctx.message.channel.id not in self.config.karma_banned_channels
            and ctx.message.channel.id != self.config.meme_repost_room
            and self.config.karma_ban_role_id not in map(lambda x: x.id, ctx.member.roles)
        ):
            emoji = utils.str_emoji_id(ctx.emoji)
            KarmaDB.karma_emoji(ctx.message.author.id, ctx.member.id, emoji)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        ctx: ReactionContext = await ReactionContext.from_payload(self.bot, payload)
        if ctx is None:
            return

        if (
            ctx.member.id != ctx.message.author.id
            and ctx.guild.id == self.config.guild_id
            and ctx.message.channel.id not in self.config.karma_banned_channels
            and ctx.message.channel.id != self.config.meme_repost_room
            and self.config.karma_ban_role_id not in map(lambda x: x.id, ctx.member.roles)
        ):
            emoji = utils.str_emoji_id(ctx.emoji)
            KarmaDB.karma_emoji_remove(ctx.message.author.id, ctx.member.id, emoji)

    @cooldowns.default_cooldown
    @commands.slash_command(name="karma", guild_ids=[Base.config.guild_id])
    async def _karma(self, inter):
        pass

    @_karma.sub_command(description=Messages.karma_brief)
    async def me(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.send_message(
            self.karma_helper.karma_get(inter.author),
            ephemeral=self.check.botroom_check(inter)
        )

    @commands.user_command(name="Karma uživatele")
    async def stalk_app(self, inter: disnake.UserCommandInteraction, user: disnake.Member):
        await inter.response.send_message(
            self.karma_helper.karma_get(inter.author, user),
            ephemeral=self.check.botroom_check(inter)
        )

    @_karma.sub_command(description=Messages.karma_stalk_brief)
    async def stalk(self, inter: disnake.ApplicationCommandInteraction, user: disnake.User):
        await inter.response.send_message(
            self.karma_helper.karma_get(inter.author, user),
            ephemeral=self.check.botroom_check(inter)
        )

    @commands.cooldown(rate=1, per=300.0, type=commands.BucketType.guild)
    @_karma.sub_command(description=Messages.karma_getall_brief)
    async def getall(self, inter: disnake.ApplicationCommandInteraction):
        await inter.send(
            Messages.karma_getall_response,
            ephemeral=self.check.botroom_check(inter)
        )
        await self.karma_helper.emoji_list_all_values(inter, self.check.botroom_check(inter))

    @_karma.sub_command(description=Messages.karma_get_brief)
    async def get(self, inter: disnake.ApplicationCommandInteraction, emoji):
        await self.karma_helper.emoji_get_value(
            inter,
            emoji,
            ephemeral=self.check.botroom_check(inter)
        )

    @cooldowns.long_cooldown
    @commands.message_command(name="Karma zprávy", guild_ids=[Base.config.guild_id])
    async def message_app(self, inter: disnake.MessageCommandInteraction, message: disnake.Message):
        await self._message(inter, message, ephemeral=self.check.botroom_check(inter))

    @cooldowns.long_cooldown
    @_karma.sub_command(description=Messages.karma_message_brief)
    async def message(self, inter: disnake.ApplicationCommandInteraction, message: disnake.Message):
        await self._message(inter, message)

    async def _message(
        self, inter: disnake.ApplicationCommandInteraction,
        message: disnake.Message,
        ephemeral: bool = False
    ):
        await inter.response.defer(with_message=True, ephemeral=ephemeral)
        embed = await self.karma_helper.message_karma(inter.author, message)
        await inter.edit_original_response(embed=embed)
        msg = await inter.original_message()
        if not ephemeral:
            await msg.add_reaction("🔁")

    @cooldowns.long_cooldown
    @_karma.sub_command(name="leaderboard", description=Messages.karma_leaderboard_brief)
    async def leaderboard(
        self,
        inter: disnake.ApplicationCommandInteraction,
        direction: str = commands.Param(default="descending", choices=["ascending", "descending"]),
        start: int = commands.Param(default=1, gt=0, lt=100000000, description=Messages.karma_board_start)
    ):
        """
        Get karma leaderboard
        """
        await inter.response.defer(ephemeral=self.check.botroom_check(inter))

        if direction == "descending":
            query = KarmaDB.leaderboard_query(KarmaDB.karma.desc())
            title = "KARMA LEADERBOARD"
            emote = "trophy"
        else:
            query = KarmaDB.leaderboard_query(KarmaDB.karma.asc())
            title = "KARMA LEADERBOARD REVERSED"
            emote = "coolStoryBob"

        embed = disnake.Embed()
        value_num = math.ceil(start / self.config.karma_grillbot_leaderboard_size)
        value = Messages.karma_web if value_num == 1 else f"{Messages.karma_web}{value_num}"
        embed.add_field(name=Messages.karma_web_title, value=value)
        page_source = LeaderboardPageSource(
            bot=self.bot,
            author=inter.author,
            query=query,
            row_formatter=self._leaderboard_formatter,
            base_embed=embed,
            title=title,
            emote_name=emote,
            member_id_col_name="member_ID",
        )

        page_num = page_source.get_page_number(start)
        page = page_source.get_page(page_num)
        embed = page_source.format_page(page)

        view = EmbedView(inter.author, embeds=[embed], page_source=page_source)
        await inter.edit_original_response(embed=embed, view=view)
        view.message = await inter.original_message()

    @cooldowns.long_cooldown
    @_karma.sub_command(name="givingboard", description=Messages.karma_givingboard_brief)
    async def givingboard(
        self,
        inter: disnake.ApplicationCommandInteraction,
        karma: str = commands.Param(default="positive", choices=["positive", "negative"]),
        direction: str = commands.Param(default="descending", choices=["ascending", "descending"]),
        start: int = commands.Param(default=1, gt=0, lt=100000000, description=Messages.karma_board_start)
    ):
        """
        Get the biggest positive/negative karma givers
        """
        await inter.response.defer(ephemeral=self.check.botroom_check(inter))

        karma_column = KarmaDB.positive if karma == "positive" else KarmaDB.negative
        order_karma = karma_column.desc() if direction == "descending" else karma_column.asc()
        query = KarmaDB.leaderboard_query(order_karma)
        formatter = self._positive_formatter if karma == "positive" else self._negative_formatter
        title = "KARMA GIVINGBOARD" if karma == "positive" else "KARMA NEGATIVE GIVINGBOARD"
        emote = "peepolove" if karma == "positive" else "gasbutton"

        page_source = LeaderboardPageSource(
            bot=self.bot,
            author=inter.author,
            query=query,
            row_formatter=formatter,
            title=title,
            emote_name=emote,
            member_id_col_name="member_ID",
        )

        page_num = page_source.get_page_number(start)
        page = page_source.get_page(page_num)
        embed = page_source.format_page(page)
        view = EmbedView(inter.author, embeds=[embed], page_source=page_source)
        await inter.edit_original_response(embed=embed, view=view)
        view.message = await inter.original_message()

    @commands.check(permission_check.is_bot_admin)
    @commands.slash_command(name="karma_mod", description=Messages.karma_brief)
    async def _karma_mod(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @commands.check(room_check.is_in_voteroom)
    @_karma_mod.sub_command(name="revote", description=Messages.karma_revote_brief)
    async def revote(self, inter: disnake.ApplicationCommandInteraction, emoji):
        """Start a revote of the karma value for emojis."""
        await inter.response.defer(ephemeral=True)
        await self.karma_helper.emoji_revote_value(inter, emoji)

    @commands.check(room_check.is_in_voteroom)
    @_karma_mod.sub_command(name="vote", description=Messages.karma_vote_brief)
    async def vote(self, inter: disnake.ApplicationCommandInteraction):
        """Start a vote using emojis without a karma value."""
        await inter.response.defer(ephemeral=True)
        await self.karma_helper.emoji_vote_value(inter)

    @_karma_mod.sub_command(name="give", description=Messages.karma_give_brief)
    async def give(
        self,
        inter: disnake.ApplicationCommandInteraction,
        users: str,
        karma: int
    ):
        await inter.response.defer()
        await self.karma_helper.karma_give(inter, users, karma)

    @_karma_mod.sub_command(name="transfer", description=Messages.karma_transfer_brief)
    async def transfer(
        self,
        inter: disnake.ApplicationCommandInteraction,
        from_user: disnake.Member,
        to_user: disnake.Member
    ):
        await inter.response.defer()
        if from_user == to_user:
            await inter.send(Messages.karma_transfer_same_user)
            return
        await self.karma_helper.karma_transfer(inter, from_user, to_user)

    @cooldowns.default_cooldown
    @commands.guild_only()
    async def karma(self, ctx: commands.Context):
        if not (self.config.guild_id == ctx.guild.id):
            await ctx.reply(Messages.server_warning)
            return
        command_id = utils.get_command_id(self, "karma")
        await ctx.reply(Messages.moved_command(name="karma", id=command_id))

    @tasks.loop(minutes=int(Base.config.grillbot_api_karma_sync_interval))
    async def sync_with_grillbot_task(self):
        items = list(KarmaDB.leaderboard_query(KarmaDB.karma.asc()))
        for chunk in utils.split_to_parts(items, 500):
            await self.grillbot_api.post_karma_store(chunk)

    @revote.error
    @vote.error
    async def karma_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.CheckFailure):
            vote_room = self.bot.get_channel(self.config.vote_room)
            await inter.send(Messages.vote_room_only(room=vote_room.mention))
            return True


def setup(bot):
    bot.add_cog(Karma(bot))
