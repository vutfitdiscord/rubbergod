"""
This builds on what discord-ext-menus does but for our usecase.

That is - getting data from database, where the pagination info
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
from config import app_config

config = app_config.Config()

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
            How many elements are in a page.
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
        # has to be a method, not property
        return self._get_max_pages

    async def get_page(self, page_number) -> DatabasePage:
        # result of this is passed into format_page(..., page) arg
        self.current_page = page_number
        return self._query.limit(self.per_page).offset(self.current_page * self.per_page).all()

    def is_paginating(self) -> bool:
        return (self.current_page + 1) < self.get_max_pages()

    def format_page(self, menu: Menu, page: DatabasePage) -> Union[str, discord.Embed, dict]:
        raise NotImplemented


base_leaderboard_format_str = "_{position}._ - **{member_name}**:"


class LeaderboardPageSource(DatabaseIteratorPageSource):
    base_embed = None

    def __init__(
            self,
            row_formatter: Union[str, Callable],
            query: Query,
            per_page=10,
            base_embed: discord.Embed = None,
    ):
        """
        Initialize this page source.

        row_formatter: :class:`str` or :class:`Callable`
            These are always supplied as keywords either into
            ``str.format`` or call of the ``formatter``:
                - ``position`` :class:`int`
                - ``member_name`` :class:`str`
                - ``entry`` :class:`Table`

        base_embed: :class:`discord.Embed`, defaults to empty Embed
            The embed that will be used as a foundation for the message,
            it's ``.description`` and ``.footer`` will be used
            for the pagination purposes.

        Warning: The table entry returned by the underlying ``Query`` has to contain
            ``member_id/_ID`` column.
        """
        self.row_formatter: Union[str, Callable] = row_formatter
        self.base_embed = base_embed if base_embed else discord.Embed()

        super().__init__(query=query, per_page=per_page)

    @staticmethod
    async def _get_member_name(ctx: Context, member_id: Union[str, int]) -> str:
        member = ctx.guild.get_member(member_id)
        if not member:
            return "_User left_"
        return discord.utils.escape_markdown(str(member))

    async def _format_row(self, entry: Table, position: int, ctx: Context) -> str:
        """
        Applies current query results onto self.row_formatter.
        The result's member_id/ID attribute value is converted into string and available
        as member_name keyword for the formatter.

        :raises :class:`AssertionError`:
            If neither ``member_id`` nor ``member_ID`` column is found in data returned from query.
        :returns: Formatted string, result of calling/applying `self.row_formatter`.
        """

        # try to guess member_id key
        member_id = getattr(entry, "member_id", None) or getattr(entry, "member_ID", None)
        assert member_id, f"Table {entry} row does not contain member_id/_ID."
        member_name = await self._get_member_name(ctx, member_id)

        kwargs = {"position": position, "member_name": member_name, "entry": entry}

        if type(self.row_formatter) == str:
            return self.row_formatter.format_map(kwargs)

        return self.row_formatter(**kwargs)

    async def format_page(self, menu, page: DatabasePage) -> Union[str, discord.Embed, dict]:
        lines = []

        for i, entry in enumerate(page):  # type: int, Table
            lines.append(await self._format_row(entry, (self.current_page * self.per_page) + i + 1, menu.ctx))

        self.base_embed.description = "\n" + "\n".join(lines)

        # possibility to optimize, author should be set only once
        utils.add_author_footer(
            self.base_embed, menu.ctx, additional_text=(f"{self.current_page + 1}/{self.get_max_pages()} pages.",)
        )

        return self.base_embed
