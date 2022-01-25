"""
Custom data sources for menus

This builds on what discord-ext-menus does but for our usage.
Which is - getting data from database, where the pagination info
goes directly down to the used database query (with .offset, .limit),
whereas the already implemented ones only work with iterables/generators of the data.

We also need the command ctx to populate some values (member_ID) from discord.
"""

import math
from functools import cached_property
from typing import Iterable, Union, Callable

import discord
from discord.ext.commands import Context
from discord.ext.menus import PageSource, Menu
from sqlalchemy.orm.query import Query
from sqlalchemy.schema import Table

import utils
from config.app_config import config

DatabasePage = Iterable[Table]


class DatabaseIteratorPageSource(PageSource):
    """A data source from sqlalchemy database query.

    This page source does not handle any sort of formatting, leaving it up
    to the user. To do so, implement the :meth:`format_page` method.
    """

    def __init__(self, query: Query, per_page=10):
        """
        query: :class:`Query`
            The query which will be realized to poll for database items.
            It MUST NOT have `.offset`, `.limit` or `.slice` already applied on it.

            Example: ``session.query(KarmaTable).order_by(KarmaTable.count)``

        per_page: :class:`int`
            How many rows to return per one page.
            Will be used on database query to poll for that amount.
        """

        self._query = query

        self.per_page = per_page
        self.current_page = 0

    @cached_property
    def _get_max_pages(self):
        # .count() might be slow
        # https://stackoverflow.com/q/14754994/5881796
        count = self._query.count()
        return math.ceil(count / self.per_page) if count > 0 else 0

    def get_max_pages(self):
        return self._get_max_pages

    async def get_page(self, page_number) -> DatabasePage:
        # result of this is passed into format_page(..., page) arg
        self.current_page = page_number
        return self._query.limit(self.per_page).offset(self.current_page * self.per_page).all()

    def is_paginating(self) -> bool:
        # Do not show pagination controls if there is only one page
        return (self.current_page + 1) < self.get_max_pages()

    def format_page(self, menu: Menu, page: DatabasePage) -> Union[str, discord.Embed, dict]:
        raise NotImplemented


class LeaderboardPageSource(DatabaseIteratorPageSource):
    """
    Page source for menus with leaderboard-like structure,
    builds on top of database iterator and abstracts formatting
    of the query data into strings (leaderboard rows).

    This is a final class that shouldn't have to be subclassed,
    as most of the possible leaderboard params can be supplied as
    init args.
    """
    base_embed: discord.Embed = None
    member_id_col_name: str = None

    def __init__(
            self,
            row_formatter: Union[str, Callable],
            query: Query,
            per_page=10,
            base_embed: discord.Embed = None,
            member_id_col_name="member_id",
    ):
        """
        Initialize this page source.

        row_formatter: Format :class:`str` or :class:`Callable`.
            These are always supplied as formatting keywords (or just keyword args for callables).
                - ``position`` :class:`int`
                - ``member_name`` :class:`str`
                - ``entry`` :class:`Table`

        base_embed: :class:`discord.Embed` defaults to empty Embed.
            The embed that will be used as a foundation for the message,
            it's ``.description`` and ``.footer`` will be used
            for the pagination purposes.

        Notice:
            The table entry returned by the underlying ``Query`` has to contain
            ``member_id/_ID`` column.
        """

        if type(row_formatter) == str:
            self.row_formatter = lambda **kw: row_formatter.format_map(kw)
        elif callable(row_formatter):
            self.row_formatter = row_formatter
        else:
            raise Exception("row_formatter has invalid type, should be str or callable.")

        self.base_embed = base_embed if base_embed else discord.Embed()
        self.member_id_col_name = member_id_col_name
        super().__init__(query=query, per_page=per_page)

    @staticmethod
    async def _get_member_name(ctx: Context, member_id: Union[str, int]) -> str:
        if ctx.guild:
            member = ctx.guild.get_member(member_id)
        else:
            guild = ctx.bot.get_guild(config.guild_id)
            member = guild.get_member(member_id)
        if not member:
            return "_User left_"
        return discord.utils.escape_markdown(str(member))

    async def _format_row(self, entry: Table, position: int, ctx: Context) -> str:
        """
        Applies current query results onto self.row_formatter.
        The entry's member id attribute is converted and available
        as member_name keyword for the formatter.

        :raises :class:`AssertionError`:
            If the specified member id column can't be found in entry
        :returns: Formatted string, result of calling/applying `self.row_formatter`.
        """

        member_id = getattr(entry, self.member_id_col_name, None)
        assert member_id, f"Table {entry} row does not contain '{self.member_id_col_name}'?"

        member_name = await self._get_member_name(ctx, member_id)

        kwargs = {"position": position, "member_name": member_name, "entry": entry}
        return self.row_formatter(**kwargs)

    async def format_page(self, menu, page: DatabasePage) -> Union[str, discord.Embed, dict]:
        board_lines = []

        for i, entry in enumerate(page):  # type: int, Table
            board_lines.append(await self._format_row(
                entry=entry, position=(self.current_page * self.per_page) + i + 1, ctx=menu.ctx
            ))

        self.base_embed.description = "\n" + "\n".join(board_lines)

        # possibility to optimize, author could be set only once
        utils.add_author_footer(
            self.base_embed,
            menu.ctx.author,
            additional_text=(f"{self.current_page + 1}/{self.get_max_pages()} pages.",),
        )

        return self.base_embed
