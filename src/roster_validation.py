"""Checks the roster sheet matches SheetLayout before anything is parsed or sent to Kronos."""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta

from openpyxl.utils import get_column_letter

import config
from config import SheetLayout
from excel_workbook import ExcelWorkbook
from models import PayCodeEntry, Shift
from roster_parser import (
    TIME_RANGE_REGEX, ParsedRoster, Sheet, employee_rows, is_ignored, parse_cell, parse_roster, read_date,
)


FORMULA_HINT = "If these cells are formulas, open and save the file in Excel so their values are stored."
SHIFTED_HINT = "Has a column been added or removed?"


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)  # stop the run
    warnings: list[str] = field(default_factory=list)  # printed, run continues

    @property
    def ok(self) -> bool:
        return not self.errors

    def print(self):
        for warning in self.warnings:
            print(f"WARNING: {warning}")
        for error in self.errors:
            print(f"ERROR: {error}")


def load_valid_roster(file_path: str, layout: SheetLayout, start_day_offset: int = 0) -> ParsedRoster | None:
    """Open, check and parse the roster. Prints any problems and returns None if there are errors."""
    workbook = ExcelWorkbook(file_path, layout.sheet_name)
    report = validate_roster(workbook, layout, start_day_offset)
    report.print()
    if not report.ok:
        return None
    return parse_roster(workbook, layout, start_day_offset)


def validate_roster(sheet: Sheet, layout: SheetLayout, start_day_offset: int = 0) -> ValidationReport:
    report = ValidationReport()

    if not 0 <= start_day_offset < len(layout.day_cols):
        report.errors.append(
            f"Start day offset must be between 0 and {len(layout.day_cols) - 1}, got {start_day_offset}"
        )
        return report

    _check_dates(sheet, layout, report)
    _check_names(sheet, layout, report)
    _check_name_repeat_col(sheet, layout, report)
    _check_cells(sheet, layout, start_day_offset, report)
    return report


def _ref(row: int, col: int) -> str:
    return f"{get_column_letter(col)}{row}"


def _check_dates(sheet: Sheet, layout: SheetLayout, report: ValidationReport):
    """Every day column has a date, and they run one day apart."""
    dates: list[date] = []
    bad_cols: list[int] = []
    for col in layout.day_cols:
        try:
            dates.append(read_date(sheet, layout.date_row, col))
        except ValueError:
            bad_cols.append(col)

    if len(bad_cols) == len(layout.day_cols):
        first, last = _ref(layout.date_row, layout.day_cols[0]), _ref(layout.date_row, layout.day_cols[-1])
        report.errors.append(f"No dates in {first}:{last}. {FORMULA_HINT}")
        return
    if bad_cols:
        cells = ", ".join(f"{_ref(layout.date_row, c)} ({sheet.get_cell_value(layout.date_row, c)!r})" for c in bad_cols)
        report.errors.append(f"Expected dates in {cells}. {SHIFTED_HINT}")
        return

    for i, (col, day) in enumerate(zip(layout.day_cols, dates)):
        expected = dates[0] + timedelta(days=i)
        if day != expected:
            report.errors.append(f"{_ref(layout.date_row, col)} is {day}, expected {expected}. Dates must be consecutive.")
            return

    if dates[0].weekday() != 0:
        report.warnings.append(f"Roster starts on a {dates[0]:%A} ({dates[0]}), not a Monday")


def _check_names(sheet: Sheet, layout: SheetLayout, report: ValidationReport):
    """The name column holds names, each employee appears once, and exclude markers are only 'x'."""
    rows_by_name: dict[str, list[int]] = defaultdict(list)

    for row in range(layout.first_employee_row, sheet.max_row + 1):
        name = sheet.get_cell_text(row, layout.kronos_name_col).strip()
        marker = sheet.get_cell_text(row, layout.exclude_marker_col).strip()
        if not name:
            continue

        if name in config.SHIFT_TIMES or TIME_RANGE_REGEX.match(name):
            report.errors.append(
                f"{_ref(row, layout.kronos_name_col)} is {name!r}, which looks like a shift, not a name. {SHIFTED_HINT}"
            )
            return

        if marker.lower() == "x":
            continue
        if marker:
            report.warnings.append(
                f"{_ref(row, layout.exclude_marker_col)} is {marker!r}. Only 'x' excludes an employee, so {name} will be entered."
            )
        rows_by_name[name].append(row)

    if not rows_by_name:
        report.errors.append(f"No employee names in column {get_column_letter(layout.kronos_name_col)}. {FORMULA_HINT}")

    for name, rows in rows_by_name.items():
        if len(rows) > 1:
            report.errors.append(f"{name} is in rows {rows}. Only the last row's shifts would be entered.")


def _check_name_repeat_col(sheet: Sheet, layout: SheetLayout, report: ValidationReport):
    """The mid-sheet name column is where expected, so the day columns either side line up."""
    header = sheet.get_cell_text(layout.date_row, layout.name_repeat_col).strip()
    if header != layout.name_repeat_header:
        report.errors.append(
            f"{_ref(layout.date_row, layout.name_repeat_col)} should be {layout.name_repeat_header!r}, "
            f"found {header!r}. {SHIFTED_HINT}"
        )


def _check_cells(sheet: Sheet, layout: SheetLayout, start_day_offset: int, report: ValidationReport):
    """Every cell that will be entered parses and has sensible values."""
    for row, name in employee_rows(sheet, layout):
        for col in layout.day_cols[start_day_offset:]:
            text = sheet.get_cell_text(row, col).strip()
            if not text or is_ignored(text):
                continue

            try:
                entry = parse_cell(name, date.min, text)  # only contents checked
            except ValueError as e:
                report.errors.append(f"{_ref(row, col)} ({name}): {e}")
                continue

            if isinstance(entry, Shift) and not _valid_time_range(entry.time_range):
                report.errors.append(f"{_ref(row, col)} ({name}): {text!r} is not a valid time range")
            elif isinstance(entry, PayCodeEntry) and not 0 < entry.hours <= 24:
                report.errors.append(f"{_ref(row, col)} ({name}): {text!r} has {entry.hours} hours, expected 0-24")


def _valid_time_range(time_range: str) -> bool:
    """'nnnn-nnnn' where both halves are real 24h times."""
    return all(int(t[:2]) < 24 and int(t[2:]) < 60 for t in time_range.split("-"))
