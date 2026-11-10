from datetime import datetime, timedelta

from config import SheetLayout


# 4 days, with repeated name column between day 2 and 3
LAYOUT = SheetLayout(
    sheet_name="test",
    kronos_name_col=1,
    exclude_marker_col=2,
    date_row=1,
    first_employee_row=2,
    first_day_col=3,
    last_day_col=7,
    name_repeat_col=5,
    name_repeat_header="NAME",
)

START = datetime(2026, 11, 2)  # a Monday


class FakeSheet:
    def __init__(self, cells: dict[tuple[int, int], object]):
        self.cells = cells

    @property
    def max_row(self) -> int:
        return max((r for r, _ in self.cells), default=1)

    def get_cell_value(self, row: int, col: int) -> object:
        return self.cells.get((row, col))

    def get_cell_text(self, row: int, col: int) -> str:
        return str(self.cells.get((row, col)) or "")


def make_sheet(rows: list[tuple[str, str, list[str]]]) -> FakeSheet:
    """rows: (name, exclude marker, one cell per day)"""
    cells: dict[tuple[int, int], object] = {(LAYOUT.date_row, LAYOUT.name_repeat_col): LAYOUT.name_repeat_header}
    for i, col in enumerate(LAYOUT.day_cols):
        cells[(LAYOUT.date_row, col)] = START + timedelta(days=i)
    for r, (name, marker, days) in enumerate(rows, start=LAYOUT.first_employee_row):
        cells[(r, LAYOUT.kronos_name_col)] = name
        cells[(r, LAYOUT.name_repeat_col)] = name
        cells[(r, LAYOUT.exclude_marker_col)] = marker
        for col, text in zip(LAYOUT.day_cols, days):
            cells[(r, col)] = text
    return FakeSheet(cells)
