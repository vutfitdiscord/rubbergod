from sqlalchemy.schema import Table

from .source import base_leaderboard_format_str


def make_pts_column_formatter(column_name: str):
    """For leaderboards with one points column."""

    def formatter(entry: Table, **kwargs):
        return base_leaderboard_format_str.format_map(
            kwargs) + "{} pts".format(getattr(entry, column_name))

    return formatter
