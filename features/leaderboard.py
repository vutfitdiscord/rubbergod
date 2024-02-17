import math
from functools import cached_property, lru_cache
from typing import Callable, Iterable, Union

import disnake
from sqlalchemy.orm.query import Query
from sqlalchemy.schema import Table

import utils
from config.app_config import config

DatabasePage = Iterable[Table]


class DatabaseIteratorPageSource():
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

    @cached_property
    def _get_max_pages(self):
        # .count() might be slow
        # https://stackoverflow.com/q/14754994/5881796
        count = self._query.count()
        return math.ceil(count / self.per_page) if count > 0 else 0

    def get_max_pages(self):
        return self._get_max_pages

    def get_page(self, page_number) -> DatabasePage:
        # result of this is passed into format_page(..., page) arg
        self.current_page = page_number
        return self._query.limit(self.per_page).offset(self.current_page * self.per_page).all()


class LeaderboardPageSource(DatabaseIteratorPageSource):
    """
    Page source for menus with leaderboard-like structure,
    builds on top of database iterator and abstracts formatting
    of the query data into strings (leaderboard rows).

    This is a final class that shouldn't have to be subclassed,
    as most of the possible leaderboard params can be supplied as
    init args.
    """
    base_embed: disnake.Embed = None
    member_id_col_name: str = None

    def __init__(
        self,
        bot: disnake.Client,
        author: Union[disnake.Member, disnake.User],
        row_formatter: Union[str, Callable],
        query: Query,
        title: str,
        emote_name: str = None,
        per_page: int = 10,
        base_embed: disnake.Embed = None,
        member_id_col_name: str = 'member_id',
    ):
        """
        Initialize this page source.

        row_formatter: Format :class:`str` or :class:`Callable`.
            These are always supplied as formatting keywords (or just keyword args for callables).
                - ``position`` :class:`int`
                - ``member_name`` :class:`str`
                - ``entry`` :class:`Table`

        base_embed: :class:`disnake.Embed` defaults to empty Embed.
            The embed that will be used as a foundation for the message,
            it's ``.description`` and ``.footer`` will be used
            for the pagination purposes.

        Notice:
            The table entry returned by the underlying ``Query`` has to contain
            ``member_id/_ID`` column.
        """

        if isinstance(row_formatter, str):
            self.row_formatter = lambda **kw: row_formatter.format_map(kw)
        elif callable(row_formatter):
            self.row_formatter = row_formatter
        else:
            raise Exception('row_formatter has invalid type, should be str or callable.')

        self.bot = bot
        self.author = author
        self.base_embed = base_embed if base_embed else disnake.Embed()
        self.base_embed.title = self.set_leaderboard_title(title, emote_name)
        self.member_id_col_name = member_id_col_name
        self._query = query
        self.per_page = per_page
        super().__init__(query=query, per_page=per_page)

    @lru_cache(5)
    def get_default_emoji(self, emoji: str):
        return utils.get_emoji(self.bot.get_guild(config.guild_id), emoji)

    def set_leaderboard_title(self, board_name: str, emote_name: str):
        if emote_name.startswith('<') and emote_name.endswith('>'):
            emote = emote_name
        else:
            emote = self.get_default_emoji(emote_name) or f':{emote_name}:'
        return f'{emote} {board_name} {emote}'

    def _get_member_name(self, member_id: Union[str, int]) -> str:
        guild = self.bot.get_guild(config.guild_id)
        member = guild.get_member(int(member_id))
        if not member:
            return '_User left_'
        return disnake.utils.escape_markdown(member.display_name)

    def _format_row(self, entry: Table, position: int) -> str:
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

        member_name = self._get_member_name(member_id)

        kwargs = {'position': position, 'member_name': member_name, 'entry': entry}
        return self.row_formatter(**kwargs)

    def format_page(self, page: DatabasePage) -> Union[str, disnake.Embed, dict]:
        board_lines = []

        for i, entry in enumerate(page):  # type: int, Table
            board_lines.append(self._format_row(
                entry=entry, position=(self.current_page * self.per_page) + i + 1
            ))

        self.base_embed.description = '\n' + '\n'.join(board_lines)

        # possibility to optimize, author could be set only once
        utils.add_author_footer(
            self.base_embed,
            self.author,
            additional_text=(f'{self.current_page + 1}/{self.get_max_pages()} pages.',),
        )

        return self.base_embed

    def get_page_number(self, start) -> int:
        """
        Returns page number for given position in query.
        """
        last_page = self.get_max_pages()
        page_num = start//self.per_page

        # if it's last element on page we need to subtract 1 from page_num
        if start % self.per_page == 0:
            page_num -= 1

        # if page is out of range, set it to last page
        if page_num >= last_page:
            page_num = last_page - 1

        # if page is negative, set it to 0, happens with empty board
        if page_num < 0:
            page_num = 0

        return page_num
