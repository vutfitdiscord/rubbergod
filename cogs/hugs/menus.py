from features.menus import AuthorOnlyPagedMenu
from features.menus.source import LeaderboardPageSource
from features.menus.util import make_pts_column_row_formatter, base_leaderboard_format_str
from repository.database.hugs import HugsTable
from repository.hugs_repo import HugsRepository



hugs_repo = HugsRepository()


# NOTE: I took a bit of shortcut there with the formatting.
#       Like this it's pretty easy to make an error
#       because you have to "guess/know" what keywords will be
#       available inside the formatter "in future".
# TODO: Redo the formatting with some mapper objects


def _tophugs_formatter(entry: HugsTable, **kwargs):
    return (
            base_leaderboard_format_str.format_map(kwargs)
            + f" _Given:_ **{entry.given}** - _Received:_** {entry.received}**"
    )


def get_hugboard_menu(base_embed=None):
    page_source = LeaderboardPageSource(
        query=hugs_repo.get_top_all_query(), row_formatter=_tophugs_formatter, base_embed=base_embed,
    )
    return AuthorOnlyPagedMenu(source=page_source, delete_message_after=True)


_tophugged_formatter = make_pts_column_row_formatter(HugsTable.received.name)


def get_top_hugged_menu(base_embed=None):
    page_source = LeaderboardPageSource(
        query=hugs_repo.get_top_receivers_query(), row_formatter=_tophugged_formatter, base_embed=base_embed
    )
    return AuthorOnlyPagedMenu(source=page_source, delete_message_after=True)


_tophuggers_formatter = make_pts_column_row_formatter(HugsTable.given.name)


def get_top_huggers_menu(base_embed=None):
    page_source = LeaderboardPageSource(
        query=hugs_repo.get_top_givers_query(), row_formatter=_tophuggers_formatter, base_embed=base_embed
    )
    return AuthorOnlyPagedMenu(source=page_source, delete_message_after=True)
