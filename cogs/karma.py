import disnake
from disnake.ext import commands
from buttons.embed import EmbedView

import utils
import math
from config.app_config import config
from config import messages, cooldowns
from features import karma
from features.leaderboard import LeaderboardPageSource
from repository import karma_repo
from permissions import room_check, permission_check
from features.reaction_context import ReactionContext
from repository.database.karma import Karma as Database_karma
from cogs.grillbot_api import GrillbotApi


karma_r = karma_repo.KarmaRepository()
messages = messages.Messages


class Karma(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.karma = karma.Karma(bot, karma_r)
        self.check = room_check.RoomCheck(bot)
        self.grillbot_api = GrillbotApi(bot)
        self._leaderboard_formatter = utils.make_pts_column_row_formatter(Database_karma.karma.name)
        self._positive_formatter = utils.make_pts_column_row_formatter(Database_karma.positive.name)
        self._negative_formatter = utils.make_pts_column_row_formatter(Database_karma.negative.name)

    async def handle_reaction(self, ctx: ReactionContext):
        # handle karma vote
        if ctx.message.content.startswith(messages.karma_vote_message_hack):
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
                embed = await self.karma.message_karma(ctx.member, message)
                await ctx.message.edit(embed=embed)
        # handle karma
        elif (
            ctx.member.id != ctx.message.author.id
            and ctx.guild.id == config.guild_id
            and ctx.message.channel.id not in config.karma_banned_channels
            and ctx.message.channel.id != config.meme_repost_room
            and config.karma_ban_role_id not in map(lambda x: x.id, ctx.member.roles)
        ):
            member_giver = karma_r.get_karma_object(ctx.member.id)
            member_getter = karma_r.get_karma_object(ctx.message.author.id)

            if isinstance(ctx.emoji, str):
                karma_r.karma_emoji(ctx.message.author.id, ctx.member.id, ctx.emoji)
                await self.grillbot_api.post_karma_store([member_getter, member_giver])
            else:
                karma_r.karma_emoji(ctx.message.author.id, ctx.member.id, ctx.emoji.id)
                await self.grillbot_api.post_karma_store([member_getter, member_giver])

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        ctx: ReactionContext = await ReactionContext.from_payload(self.bot, payload)
        if ctx is None:
            return

        if (
            ctx.member.id != ctx.message.author.id
            and ctx.guild.id == config.guild_id
            and ctx.message.channel.id not in config.karma_banned_channels
            and ctx.message.channel.id != config.meme_repost_room
            and config.karma_ban_role_id not in map(lambda x: x.id, ctx.member.roles)
        ):
            member_giver = karma_r.get_karma_object(ctx.member.id)
            member_getter = karma_r.get_karma_object(ctx.message.author.id)

            if isinstance(ctx.emoji, str):
                karma_r.karma_emoji_remove(ctx.message.author.id, ctx.member.id, ctx.emoji)
                await self.grillbot_api.post_karma_store([member_getter, member_giver])
            else:
                karma_r.karma_emoji_remove(ctx.message.author.id, ctx.member.id, ctx.emoji.id)
                await self.grillbot_api.post_karma_store([member_getter, member_giver])

    @cooldowns.default_cooldown
    @commands.slash_command(name="karma", guild_ids=[config.guild_id])
    async def _karma(self, inter):
        pass

    @cooldowns.default_cooldown
    @_karma.sub_command(description=messages.karma_brief)
    async def me(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.send_message(self.karma.karma_get(inter.author))
        await self.check.botroom_check(inter)

    @commands.user_command(name="Karma uživatele")
    async def stalk_app(self, inter: disnake.UserCommandInteraction, user: disnake.Member):
        ephemeral = inter.channel_id != config.bot_room
        await inter.response.send_message(self.karma.karma_get(inter.author, user), ephemeral=ephemeral)

    @_karma.sub_command(description=messages.karma_stalk_brief)
    async def stalk(self, inter: disnake.ApplicationCommandInteraction, user: disnake.User):
        await inter.response.send_message(self.karma.karma_get(inter.author, user))
        await self.check.botroom_check(inter)

    @commands.cooldown(rate=1, per=300.0, type=commands.BucketType.guild)
    @_karma.sub_command(description=messages.karma_getall_brief)
    async def getall(self, inter: disnake.ApplicationCommandInteraction):
        try:
            await inter.response.send_message(messages.karma_getall_response)
            await self.karma.emoji_list_all_values(inter.channel)
            await self.check.botroom_check(inter)
        except disnake.errors.Forbidden:
            return

    @cooldowns.default_cooldown
    @_karma.sub_command(description=messages.karma_get_brief)
    async def get(self, inter: disnake.ApplicationCommandInteraction, emoji):
        try:
            await self.karma.emoji_get_value(inter, emoji)
            await self.check.botroom_check(inter)
        except disnake.errors.Forbidden:
            return

    @commands.message_command(name="Karma zprávy")
    async def message_app(self, inter: disnake.MessageCommandInteraction, message: disnake.Message):
        ephemeral = inter.channel_id != config.bot_room
        await self._message(inter, message, ephemeral=ephemeral)

    @cooldowns.long_cooldown
    @_karma.sub_command(description=messages.karma_message_brief)
    async def message(self, inter: disnake.ApplicationCommandInteraction, message: disnake.Message):
        await self._message(inter, message)

    async def _message(
        self, inter: disnake.ApplicationCommandInteraction,
        message: disnake.Message,
        ephemeral: bool = False
    ):
        await inter.response.defer(with_message=True, ephemeral=ephemeral)
        embed = await self.karma.message_karma(inter.author, message)
        await inter.edit_original_response(embed=embed)
        msg = await inter.original_message()
        if not ephemeral:
            await msg.add_reaction("🔁")

    @cooldowns.default_cooldown
    @commands.group()
    async def karma(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            command_id = utils.get_command_id(self, "karma")
            await ctx.reply(utils.fill_message("moved_command", name="karma", id=command_id))

    @commands.check(permission_check.is_bot_admin)
    @karma.command(brief=messages.karma_revote_brief)
    async def revote(self, ctx, *args):
        if not await self.check.guild_check(ctx.message):
            await ctx.reply(messages.server_warning)
        else:
            if ctx.message.channel.id == config.vote_room:
                try:
                    await ctx.message.delete()
                    await self.karma.emoji_revote_value(ctx.message)
                except disnake.errors.Forbidden:
                    return
            else:
                dc_vote_room = disnake.utils.get(ctx.guild.channels, id=config.vote_room)
                await ctx.reply(utils.fill_message("vote_room_only", room=dc_vote_room))

    @commands.check(permission_check.is_bot_admin)
    @karma.command(brief=messages.karma_vote_brief)
    async def vote(self, ctx, *args):
        if not await self.check.guild_check(ctx.message):
            await ctx.reply(messages.server_warning)
        else:
            if ctx.message.channel.id == config.vote_room:
                try:
                    await ctx.message.delete()
                    await self.karma.emoji_vote_value(ctx.message)
                except disnake.errors.Forbidden:
                    return
            else:
                dc_vote_room = disnake.utils.get(ctx.guild.channels, id=config.vote_room)
                await ctx.reply(utils.fill_message("vote_room_only", room=dc_vote_room))

    @commands.check(permission_check.is_bot_admin)
    @karma.command(brief=messages.karma_give_brief)
    async def give(self, ctx, *args):
        await self.karma.karma_give(ctx.message)

    @commands.check(permission_check.is_bot_admin)
    @karma.command(brief=messages.karma_transfer_brief)
    async def transfer(self, ctx, *args):
        await self.karma.karma_transfer(ctx.message)

    @cooldowns.long_cooldown
    @_karma.sub_command(name="leaderboard", description=messages.karma_leaderboard_brief)
    async def leaderboard(self, inter: disnake.ApplicationCommandInteraction, start: int = 1):
        if not await self.validate_leaderboard_offset(start, inter):
            return
        embed = disnake.Embed()
        value_num = math.ceil(start / config.karma_grillbot_leaderboard_size)
        value = messages.karma_web if value_num == 1 else f"{messages.karma_web}{value_num}"
        embed.add_field(name=messages.karma_web_title, value=value)
        page_source = LeaderboardPageSource(
            bot=self.bot,
            author=inter.author,
            query=karma_r.leaderboard_query(Database_karma.karma.desc()),
            row_formatter=self._leaderboard_formatter,
            base_embed=embed,
            title='KARMA LEADERBOARD',
            emote_name='trophy',
            member_id_col_name='member_ID',
        )
        page_num = math.floor(start/page_source.per_page)
        page = page_source.get_page(page_num)
        embed = page_source.format_page(page)

        await self.check.botroom_check(inter)
        view = EmbedView(inter.author, embeds=[embed], page_source=page_source)
        await inter.response.send_message(embed=embed, view=view)
        view.message = await inter.original_message()

    @cooldowns.long_cooldown
    @_karma.sub_command(name="bajkarboard", description=messages.karma_bajkarboard_brief)
    async def bajkarboard(self, inter: disnake.ApplicationCommandInteraction, start: int = 1):
        if not await self.validate_leaderboard_offset(start, inter):
            return

        page_source = LeaderboardPageSource(
            bot=self.bot,
            author=inter.author,
            query=karma_r.leaderboard_query(Database_karma.karma),
            row_formatter=self._leaderboard_formatter,
            title='KARMA BAJKARBOARD',
            emote_name='coolStoryBob',
            member_id_col_name='member_ID',
        )
        page_num = math.floor(start/page_source.per_page)
        page = page_source.get_page(page_num)
        embed = page_source.format_page(page)

        await self.check.botroom_check(inter)
        view = EmbedView(inter.author, embeds=[embed], page_source=page_source)
        await inter.response.send_message(embed=embed, view=view)
        view.message = await inter.original_message()

    @cooldowns.long_cooldown
    @_karma.sub_command(name="givingboard", description=messages.karma_givingboard_brief)
    async def givingboard(self, inter: disnake.ApplicationCommandInteraction, start: int = 1):
        if not await self.validate_leaderboard_offset(start, inter):
            return

        page_source = LeaderboardPageSource(
            bot=self.bot,
            author=inter.author,
            query=karma_r.leaderboard_query(Database_karma.positive.desc()),
            row_formatter=self._positive_formatter,
            title='KARMA GIVINGBOARD',
            emote_name='peepolove',
            member_id_col_name='member_ID',
        )
        page_num = math.floor(start/page_source.per_page)
        page = page_source.get_page(page_num)
        embed = page_source.format_page(page)

        await self.check.botroom_check(inter)
        view = EmbedView(inter.author, embeds=[embed], page_source=page_source)
        await inter.response.send_message(embed=embed, view=view)
        view.message = await inter.original_message()

    @cooldowns.long_cooldown
    @_karma.sub_command(name="ishaboard", description=messages.karma_ishaboard_brief)
    async def ishaboard(self, inter: disnake.ApplicationCommandInteraction, start: int = 1):
        if not await self.validate_leaderboard_offset(start, inter):
            return

        page_source = LeaderboardPageSource(
            bot=self.bot,
            author=inter.author,
            query=karma_r.leaderboard_query(Database_karma.negative.desc()),
            row_formatter=self._negative_formatter,
            title='KARMA ISHABOARD',
            emote_name='<:ishagrin:638277508651024394>',
            member_id_col_name='member_ID',
        )
        page_num = math.floor(start/page_source.per_page)
        page = page_source.get_page(page_num)
        embed = page_source.format_page(page)

        await self.check.botroom_check(inter)
        view = EmbedView(inter.author, embeds=[embed], page_source=page_source)
        await inter.response.send_message(embed=embed, view=view)
        view.message = await inter.original_message()

    @revote.error
    @vote.error
    @give.error
    @transfer.error
    @stalk.error
    @message.error
    async def karma_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.MessageNotFound):
            await inter.response.send_message(
                utils.fill_message("karma_message_format", user=inter.author.id)
            )
            return True
        if isinstance(error, commands.CheckFailure):
            await inter.reply(utils.fill_message("insufficient_rights", user=inter.author.id))
            return True
        if isinstance(error, commands.UserNotFound):
            await inter.send(utils.fill_message("user_not_found", user=inter.author.id))
            return True

    async def validate_leaderboard_offset(self, offset: int, inter) -> bool:
        if not 0 < offset < 100000000:  # Any value larger than the server
            # user cnt and lower than 32bit
            # int max will do
            await inter.response.send_message(
                utils.fill_message("karma_leaderboard_offset_error", user=inter.author.id)
            )
            return False

        return True


def setup(bot):
    bot.add_cog(Karma(bot))
