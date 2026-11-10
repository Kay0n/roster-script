from datetime import date

import pytest

import config
from fake_sheet import LAYOUT, make_sheet
from models import PayCodeEntry, Shift
from roster_parser import is_ignored, parse_cell, parse_roster


DAY = date(2026, 11, 2)


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

def test_day_cols_skip_name_repeat_col():
    assert LAYOUT.day_cols == [3, 4, 6, 7]


def test_parse_roster_reads_entries_with_dates():
    sheet = make_sheet([("Smith, A", "", ["AM", "", "O", "AL/7.5"])])
    roster = parse_roster(sheet, LAYOUT)

    assert (roster.start_date, roster.end_date) == (date(2026, 11, 2), date(2026, 11, 5))
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
