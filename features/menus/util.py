from sqlalchemy.schema import Table

base_leaderboard_format_str = "_{position}._ - **{member_name}**:"


def make_pts_column_row_formatter(pts_column_name: str):
    """For leaderboards with one column of points."""

    def formatter(entry: Table, **kwargs):
        return base_leaderboard_format_str.format_map(
            kwargs) + " {} pts".format(getattr(entry, pts_column_name))

    return formatter
