from textwrap import wrap
from typing import Optional

from prettytable import PrettyTable


class TableGenerator:
    DEFAULT_WIDTH = 20

    def __init__(self, header: list[str], column_width: int = DEFAULT_WIDTH):
        self.table = PrettyTable()
        self.header = header
        self.table.field_names = header
        self.column_width = column_width

    def align(self, aligns: list[str]):
        """Aligns columns in table, default is all center. Possible values: l, c, r."""
        for idx, field in enumerate(self.header):
            self.table.align[field] = aligns[idx]

    def generate_table(self, matrix: list[list[str]]) -> str:
        """Generates table from matrix, wraps long strings."""

        def wrap_text(elem: str) -> Optional[list[str]]:
            if len(elem) > self.column_width:
                return wrap(elem[self.column_width :], width=self.column_width)
            return []

        for row in matrix:
            new_row_cnt = 0
            new_row = [[]] * len(row)
            # Wrap long strings
            for idx in range(len(row)):
                # Wrap long strings
                new_row[idx] = wrap_text(row[idx])
                # Get number of rows to add to table because of wrapping
                new_row_cnt = len(new_row[idx]) if len(new_row[idx]) > new_row_cnt else new_row_cnt
                # Cut long strings
                row[idx] = row[idx][: self.column_width]

            # add original row
            self.table.add_row(row, divider=(new_row_cnt == 0))

            # add wrapped rows
            if new_row_cnt > 0:
                for i in range(new_row_cnt):
                    # rotate new_row matrix and add to table, fill gaps with empty strings
                    self.table.add_row(
                        [new_row[j][i] if len(new_row[j]) > i else "" for j in range(len(new_row))],
                        divider=(i == new_row_cnt - 1),
                    )

        return self.table.get_string()
