"""
Cog implementing hug commands. Send hug to user and see leaderboard.
"""

import disnake
from disnake.ext import commands

import utils
from buttons.embed import PaginationView
from cogs.base import Base
from database.hugs import HugsTableDB
from features.leaderboard import LeaderboardPageSource
from rubbergod import Rubbergod
from utils import cooldowns
from utils.checks import PermissionsCheck
from utils.general import make_pts_column_row_formatter

from .messages_cz import MessagesCZ


def _tophugs_formatter(entry: HugsTableDB, **kwargs):
    return (
        MessagesCZ.base_leaderboard_format_str.format_map(kwargs)
        + f" _Given:_ **{entry.given}** - _Received:_** {entry.received}**"
    )


class Hugs(Base, commands.Cog):
    """
    Hugging commands.
    """

    emoji_count = len(Base.config.hug_emojis)

    def __init__(self, bot: Rubbergod):
        super().__init__()
        self.bot = bot
        self.hugs_db = HugsTableDB()
        self._tophuggers_formatter = make_pts_column_row_formatter(HugsTableDB.given.name)
        self._tophugged_formatter = make_pts_column_row_formatter(HugsTableDB.received.name)

    @commands.slash_command(name="hug")
    async def _hug(self, inter):
        pass

    @cooldowns.default_cooldown
    @_hug.sub_command(name="hugboard", description=MessagesCZ.hugboard_brief)
    async def hugboard(self, inter: disnake.ApplicationCommandInteraction):
        """
        Overall hugging stats.
        """

        await inter.response.defer(ephemeral=PermissionsCheck.is_botroom(inter))

        page_source = LeaderboardPageSource(
            bot=self.bot,
            author=inter.author,
            query=self.hugs_db.get_top_all_query(),
            row_formatter=_tophugs_formatter,
            title="HUGBOARD",
            emote_name="peepoHugger",
        )

        page = page_source.get_page(0)
        embed = page_source.format_page(page)

        view = PaginationView(inter.author, embeds=[embed], page_source=page_source)
        view.message = await inter.edit_original_response(embed=embed, view=view)

    @cooldowns.default_cooldown
    @_hug.sub_command(name="huggersboard", description=MessagesCZ.huggersboard_brief)
    async def huggersboard(self, inter: disnake.ApplicationCommandInteraction):
        """
        Get the biggest huggers.
        """

        await inter.response.defer(ephemeral=PermissionsCheck.is_botroom(inter))

        page_source = LeaderboardPageSource(
            bot=self.bot,
            author=inter.author,
            query=self.hugs_db.get_top_givers_query(),
            row_formatter=self._tophuggers_formatter,
            title="TOP HUGGERS",
            emote_name="peepoHugger",
        )

        page = page_source.get_page(0)
        embed = page_source.format_page(page)

        view = PaginationView(inter.author, embeds=[embed], page_source=page_source)
        view.message = await inter.edit_original_response(embed=embed, view=view)

    @cooldowns.default_cooldown
    @_hug.sub_command(name="mosthugged", description=MessagesCZ.mosthugged_brief)
    async def mosthugged(self, inter: disnake.ApplicationCommandInteraction):
        """
        Get the most hugged.
        """

        await inter.response.defer(ephemeral=PermissionsCheck.is_botroom(inter))

        page_source = LeaderboardPageSource(
            bot=self.bot,
            author=inter.author,
            query=self.hugs_db.get_top_receivers_query(),
            row_formatter=self._tophugged_formatter,
            title="TOP HUGGED",
            emote_name="peepoHugger",
        )

        page = page_source.get_page(0)
        embed = page_source.format_page(page)

        view = PaginationView(inter.author, embeds=[embed], page_source=page_source)
        view.message = await inter.edit_original_response(embed=embed, view=view)

    @cooldowns.default_cooldown
    @_hug.sub_command(name="me", description=MessagesCZ.hug_stats_brief)
    async def stats(self, inter: disnake.ApplicationCommandInteraction, user: disnake.Member = None):
        """
        Get your lovely hug stats.
        """

        await inter.response.defer(ephemeral=PermissionsCheck.is_botroom(inter))

        if user is None or user == inter.author:
            user = inter.author
            user_str = user.display_name
            title = "{0} Your Lovely Hug Stats {0}"
        else:
            user_str = user.display_name
            title = f"{{0}} {user_str}'s Lovely Hug Stats {{0}}"

        stats = self.hugs_db.get_members_stats(user.id)
        positions = self.hugs_db.get_member_position(stats)
        avg_position = int((positions[0] + positions[1]) // 2)
        guild = self.bot.get_guild(self.config.guild_id)

        embed = disnake.Embed(
            title=title.format(utils.general.get_emoji(guild, "peepoHugger") or ""),
            description=" | ".join(
                (
                    "**Ranks**",
                    f"Given: **{positions[0]}.**",
                    f"Received: **{positions[1]}.**",
                    f"Avg: **{avg_position}.**",
                )
            ),
        )

        embed.set_author(name=user_str, icon_url=user.display_avatar.url)
        utils.embed.add_author_footer(embed, inter.author)

        given_emoji = utils.general.get_emoji(guild, "peepohugs") or ""
        recv_emoji = utils.general.get_emoji(guild, "huggers") or ""

        embed.add_field(name=f"{given_emoji} Given", value=str(stats.given))
        embed.add_field(name=f"{recv_emoji} Received", value=str(stats.received))

        await inter.edit_original_response(embed=embed)

    @cooldowns.short_cooldown
    @_hug.sub_command(name="give", description=MessagesCZ.hug_give_brief)
    async def give(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.Member = None,
        intensity: int = commands.Param(
            name="intensity",
            description=MessagesCZ.hug_intensity_description(emoji_count=emoji_count),
            ge=1,
            le=emoji_count,
            default=1,
        ),
    ):
        """
        Because everyone likes hugs <3
        """

        await inter.response.defer()

        if user is None:
            user = inter.author
        elif user.bot:
            await inter.send(
                utils.general.get_emoji(self.bot.get_guild(self.config.guild_id), "huggers")
                or ":people_hugging:"
            )
            return

        if user != inter.author:
            self.hugs_db.do_hug(giver_id=inter.author.id, receiver_id=user.id)

        user_str = user.display_name

        # Convert a human-friendly intensity to an array index
        intensity -= 1

        await inter.send(f"{self.config.hug_emojis[intensity]} **{user_str}**")
