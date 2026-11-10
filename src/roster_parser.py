"""Reads the roster spreadsheet into Shift / PayCodeEntry entries. No browser code here."""

import os
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Protocol

import config
from config import SheetLayout
from excel_workbook import ExcelWorkbook
from models import PayCodeEntry, RosterEntry, Shift


TIME_RANGE_REGEX = re.compile(r"^\d{4}-\d{4}$")  # nnnn-nnnn, n = digit
MAX_ROW = 300


class Sheet(Protocol):
    """What the parser needs from a workbook; lets tests pass a fake."""
    def get_cell_value(self, row: int, col: int) -> object: ...
    def get_cell_text(self, row: int, col: int) -> str: ...


@dataclass
class ParsedRoster:
    entries: dict[str, list[RosterEntry]] = field(default_factory=dict)  # employee name -> entries
    unknown_symbols: set[str] = field(default_factory=set)
    employees_processed: int = 0

    @property
    def entry_count(self) -> int:
        return sum(len(e) for e in self.entries.values())

    def print_summary(self, employee_ids: dict[str, int]):
        print("Roster ingestion complete")
        print(f"Processed {self.entry_count} entries from {self.employees_processed} employees")
        print("Unknown Symbols:")
        print(self.unknown_symbols)

        print("Employees not found in Kronos:")
        for name in self.entries:
            if name not in employee_ids:
                print(name)

    def print_entries(self):
        for name, entries in self.entries.items():
            print(name)
            for entry in entries:
                print(f"    {entry}")


def find_roster_file() -> str:
    """The single .xlsx in the current directory."""
    xlsx_files = sorted(f for f in os.listdir() if f.endswith(".xlsx"))
    if len(xlsx_files) != 1:
        raise FileNotFoundError(
            f"Expected exactly one .xlsx in {os.getcwd()}, found {xlsx_files or 'none'}. Pass one with --file."
        )
    return os.path.abspath(xlsx_files[0])


def load_roster(file_path: str, layout: SheetLayout, start_day_offset: int = 0) -> ParsedRoster:
    return parse_roster(ExcelWorkbook(file_path, layout.sheet_name), layout, start_day_offset)


def read_date_range(file_path: str, layout: SheetLayout) -> tuple[date, date]:
    """First and last day of the roster period, from the date row."""
    workbook = ExcelWorkbook(file_path, layout.sheet_name)
    return (
        read_date(workbook, layout.date_row, layout.day_cols[0]),
        read_date(workbook, layout.date_row, layout.day_cols[-1]),
    )


def read_date(sheet: Sheet, row: int, col: int) -> date:
    value = sheet.get_cell_value(row, col)
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    raise ValueError(f"Expected a date at row {row}, col {col}, found {value!r}")


def is_ignored(cell_text: str) -> bool:
    return cell_text in config.IGNORED_CELL_VALUES or any(
        pattern.match(cell_text) for pattern in config.IGNORED_CELL_PATTERNS
    )


def parse_cell(employee_name: str, day: date, cell_text: str) -> RosterEntry | None:
    if cell_text in config.SHIFT_TIMES:
        return Shift(employee_name, day, config.SHIFT_TIMES[cell_text])

    if TIME_RANGE_REGEX.match(cell_text):
        return Shift(employee_name, day, cell_text)

    paycode_split = cell_text.split("/", 1)
    code = paycode_split[0].strip()

    if code in config.PAYCODES:
        if len(paycode_split) == 1 or not paycode_split[1].strip():
            return None

        try:
            hours = float(paycode_split[1])
        except ValueError:
            raise Exception(f"Invalid hours value '{paycode_split[1]}' for paycode '{code}'")

        return PayCodeEntry(employee_name, day, config.PAYCODES[code], hours)

    return None


def parse_roster(sheet: Sheet, layout: SheetLayout, start_day_offset: int = 0) -> ParsedRoster:
    roster = ParsedRoster()
    day_cols = layout.day_cols[start_day_offset:]

    for row in range(layout.first_employee_row, MAX_ROW):
        employee_name = sheet.get_cell_text(row, layout.kronos_name_col).strip()
        if not employee_name:
            continue
        if sheet.get_cell_text(row, layout.exclude_marker_col).strip().lower() == "x":
            continue

        print(f"Processing row {row}: '{employee_name}'")
        roster.employees_processed += 1

        entries: list[RosterEntry] = []

        for col in day_cols:
            cell_text = sheet.get_cell_text(row, col).strip()
            if not cell_text or is_ignored(cell_text):
                continue

            day = read_date(sheet, layout.date_row, col)
            entry = parse_cell(employee_name, day, cell_text)

            if entry:
                entries.append(entry)
            else:
                print(f"Skipping unknown cell content: {cell_text} at row {row}, col {col}")
                roster.unknown_symbols.add(cell_text)

        if entries:
            roster.entries[employee_name] = entries

    roster.entries = dict(sorted(roster.entries.items()))
    return roster
