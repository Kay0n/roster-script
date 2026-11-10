from datetime import datetime

import pytest

from fake_sheet import LAYOUT, FakeSheet, make_sheet
from roster_validation import validate_roster


def errors_for(sheet: FakeSheet, start_day_offset: int = 0) -> list[str]:
    return validate_roster(sheet, LAYOUT, start_day_offset).errors


def good_sheet() -> FakeSheet:
    return make_sheet([
        ("Smith, A", "", ["AM", "", "AL/7.5", "0900-1700"]),
        ("Jones, B", "x", ["PM", "PM", "", ""]),
    ])


def test_good_sheet_passes():
    report = validate_roster(good_sheet(), LAYOUT)
    assert report.errors == []
    assert report.warnings == []


# --- dates ---

def test_no_dates_mentions_formulas():
    sheet = good_sheet()
    for col in LAYOUT.day_cols:
        sheet.cells[(LAYOUT.date_row, col)] = None
    [error] = errors_for(sheet)
    assert "No dates" in error and "formulas" in error


def test_missing_date():
    sheet = good_sheet()
    sheet.cells[(LAYOUT.date_row, LAYOUT.day_cols[2])] = "Mon"
    [error] = errors_for(sheet)
    assert "F1 ('Mon')" in error


def test_dates_not_consecutive():
    sheet = good_sheet()
    sheet.cells[(LAYOUT.date_row, LAYOUT.day_cols[2])] = datetime(2026, 11, 20)
    [error] = errors_for(sheet)
    assert "consecutive" in error


def test_not_starting_monday_is_warning():
    sheet = good_sheet()
    for i, col in enumerate(LAYOUT.day_cols):
        sheet.cells[(LAYOUT.date_row, col)] = datetime(2026, 11, 3 + i)
    report = validate_roster(sheet, LAYOUT)
    assert report.ok
    assert "Tuesday" in report.warnings[0]


# --- layout ---

def test_wrong_name_repeat_header():
    sheet = good_sheet()
    sheet.cells[(LAYOUT.date_row, LAYOUT.name_repeat_col)] = "Something"
    [error] = errors_for(sheet)
    assert "E1 should be 'NAME'" in error


def test_shift_in_name_column():
    sheet = good_sheet()
    sheet.cells[(2, LAYOUT.kronos_name_col)] = "AM"
    [error] = errors_for(sheet)
    assert "looks like a shift" in error


# --- names ---

def test_no_names_mentions_formulas():
    sheet = make_sheet([])
    [error] = errors_for(sheet)
    assert "No employee names" in error and "formulas" in error


def test_duplicate_names():
    sheet = make_sheet([("Smith, A", "", ["AM"]), ("Smith, A", "", ["PM"])])
    [error] = errors_for(sheet)
    assert "rows [2, 3]" in error


def test_excluded_duplicate_is_fine():
    sheet = make_sheet([("Smith, A", "", ["AM"]), ("Smith, A", "x", ["PM"])])
    assert errors_for(sheet) == []


def test_odd_exclude_marker_is_warning():
    sheet = make_sheet([("Smith, A", "y", ["AM"])])
    report = validate_roster(sheet, LAYOUT)
    assert report.ok
    assert "Only 'x' excludes" in report.warnings[0]


# --- cells ---

@pytest.mark.parametrize("text, message", [
    ("AL/abc", "Invalid hours"),
    ("AL/75", "75.0 hours"),
    ("AL/0", "0.0 hours"),
    ("2500-0700", "not a valid time range"),
    ("0660-0700", "not a valid time range"),
])
def test_bad_cells(text: str, message: str):
    sheet = make_sheet([("Smith, A", "", [text])])
    [error] = errors_for(sheet)
    assert error.startswith("C2 (Smith, A)")
    assert message in error


def test_bad_cells_before_offset_are_ignored():
    sheet = make_sheet([("Smith, A", "", ["AL/abc", "AM"])])
    assert errors_for(sheet, start_day_offset=1) == []


def test_bad_cell_in_excluded_row_is_ignored():
    sheet = make_sheet([("Smith, A", "x", ["AL/abc"])])
    assert "Invalid hours" not in " ".join(errors_for(sheet))


@pytest.mark.parametrize("offset", [-1, 4])
def test_offset_out_of_range(offset: int):
    [error] = errors_for(good_sheet(), offset)
    assert "between 0 and 3" in error
