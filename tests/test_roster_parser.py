from datetime import date, datetime, timedelta

import pytest

import config
from config import SheetLayout
from models import PayCodeEntry, Shift
from roster_parser import is_ignored, parse_cell, parse_roster


DAY = date(2026, 11, 2)

# Same shape as the real sheet, smaller: 4 days, spacer between day 2 and day 3
LAYOUT = SheetLayout(
    sheet_name="test",
    kronos_name_col=1,
    exclude_marker_col=2,
    date_row=1,
    first_employee_row=2,
    first_day_col=3,
    last_day_col=7,
    spacer_col=5,
)


class FakeSheet:
    def __init__(self, cells: dict[tuple[int, int], object]):
        self.cells = cells

    def get_cell_value(self, row: int, col: int) -> object:
        return self.cells.get((row, col))

    def get_cell_text(self, row: int, col: int) -> str:
        return str(self.cells.get((row, col)) or "")


def make_sheet(rows: list[tuple[str, str, list[str]]]) -> FakeSheet:
    """rows: (name, exclude marker, one cell per day)"""
    cells: dict[tuple[int, int], object] = {}
    for i, col in enumerate(LAYOUT.day_cols):
        cells[(LAYOUT.date_row, col)] = datetime(2026, 11, 2) + timedelta(days=i)
    for r, (name, marker, days) in enumerate(rows, start=LAYOUT.first_employee_row):
        cells[(r, LAYOUT.kronos_name_col)] = name
        cells[(r, LAYOUT.exclude_marker_col)] = marker
        for col, text in zip(LAYOUT.day_cols, days):
            cells[(r, col)] = text
    return FakeSheet(cells)


# --- parse_cell ---

def test_shift_code_uses_shift_times():
    assert parse_cell("A", DAY, "AM") == Shift("A", DAY, config.SHIFT_TIMES["AM"])


def test_literal_time_range():
    assert parse_cell("A", DAY, "0900-1700") == Shift("A", DAY, "0900-1700")


def test_paycode_with_hours():
    assert parse_cell("A", DAY, "AL/7.5") == PayCodeEntry("A", DAY, config.PAYCODES["AL"], 7.5)


def test_paycode_without_hours_is_unknown():
    assert parse_cell("A", DAY, "AL") is None
    assert parse_cell("A", DAY, "AL/") is None


def test_paycode_with_bad_hours_raises():
    with pytest.raises(Exception, match="Invalid hours"):
        parse_cell("A", DAY, "AL/abc")


def test_unknown_value():
    assert parse_cell("A", DAY, "???") is None


# --- is_ignored ---

@pytest.mark.parametrize("text", ["O", "NRM", "WK3", "WK21", "ML", "MLUP", "ML/11.5", "ML/7.5", "M/L", "RPH", "LSL"])
def test_ignored(text: str):
    assert is_ignored(text)


@pytest.mark.parametrize("text", ["AM", "AL/7.5", "WK", "MLX"])
def test_not_ignored(text: str):
    assert not is_ignored(text)


# --- parse_roster ---

def test_day_cols_skip_spacer():
    assert LAYOUT.day_cols == [3, 4, 6, 7]


def test_parse_roster_reads_entries_with_dates():
    sheet = make_sheet([("Smith, A", "", ["AM", "", "O", "AL/7.5"])])
    roster = parse_roster(sheet, LAYOUT)

    assert roster.entries == {"Smith, A": [
        Shift("Smith, A", date(2026, 11, 2), config.SHIFT_TIMES["AM"]),
        PayCodeEntry("Smith, A", date(2026, 11, 5), config.PAYCODES["AL"], 7.5),
    ]}
    assert roster.employees_processed == 1
    assert roster.entry_count == 2


def test_parse_roster_skips_excluded_and_collects_unknown():
    sheet = make_sheet([
        ("Excluded, B", "x", ["AM", "AM", "AM", "AM"]),
        ("Jones, C", "", ["???", "", "", ""]),
    ])
    roster = parse_roster(sheet, LAYOUT)

    assert roster.entries == {}
    assert roster.employees_processed == 1
    assert roster.unknown_symbols == {"???"}


@pytest.mark.parametrize("offset, first_date", [(1, date(2026, 11, 3)), (2, date(2026, 11, 4)), (3, date(2026, 11, 5))])
def test_start_day_offset_counts_days_not_columns(offset: int, first_date: date):
    sheet = make_sheet([("Smith, A", "", ["AM", "AM", "AM", "AM"])])
    entries = parse_roster(sheet, LAYOUT, offset).entries["Smith, A"]

    assert len(entries) == 4 - offset
    assert entries[0].date == first_date
