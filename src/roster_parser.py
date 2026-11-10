"""Reads the roster spreadsheet into Shift / PayCodeEntry entries. No browser code here."""

import os
import re
from dataclasses import dataclass, field
from datetime import datetime

import config
from config import SheetLayout
from excel_workbook import ExcelWorkbook
from models import PayCodeEntry, RosterEntry, Shift


TIME_RANGE_REGEX = re.compile(r"^\d{4}-\d{4}$")  # nnnn-nnnn, n = digit
MAX_ROW = 300


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
        print(f"Processed {self.entry_count} shifts from {self.employees_processed} employees")
        print("Unknown Symbols:")
        print(self.unknown_symbols)

        print("Employees not found in Kronos:")
        for name in self.entries:
            if name not in employee_ids:
                print(name)


def load_roster(layout: SheetLayout, start_day_offset: int = 0) -> ParsedRoster:
    workbook = ExcelWorkbook(find_roster_file(), layout.sheet_name)
    return parse_roster(workbook, layout, start_day_offset)


def find_roster_file() -> str:
    cwd = os.getcwd()
    for file in os.listdir(cwd):
        if file.endswith(".xlsx"):
            return os.path.join(cwd, file)
    return ""


def date_cell_to_iso(cell_text: str) -> str:
    return datetime.strptime(cell_text, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")


def parse_cell(employee_name: str, date_str: str, cell_text: str) -> RosterEntry | None:
    if cell_text in config.SHIFT_TIMES:
        return Shift(employee_name, date_str, config.SHIFT_TIMES[cell_text])

    if TIME_RANGE_REGEX.match(cell_text):
        return Shift(employee_name, date_str, cell_text)

    paycode_split = cell_text.split("/", 1)
    code = paycode_split[0].strip()

    if code in config.PAYCODES:
        if len(paycode_split) == 1 or not paycode_split[1].strip():
            return None

        try:
            hours = float(paycode_split[1])
        except ValueError:
            raise Exception(f"Invalid hours value '{paycode_split[1]}' for paycode '{code}'")

        return PayCodeEntry(employee_name, date_str, config.PAYCODES[code], hours)

    return None


def parse_roster(workbook: ExcelWorkbook, layout: SheetLayout, start_day_offset: int = 0) -> ParsedRoster:
    roster = ParsedRoster()

    start_day_col = layout.first_day_col + start_day_offset
    if start_day_col > 22:
        start_day_col += 1  # account for spacer column

    for row in range(layout.first_employee_row, MAX_ROW):
        employee_name = workbook.get_cell_text(row, layout.kronos_name_col).strip()
        if not employee_name:
            continue
        if workbook.get_cell_text(row, layout.exclude_marker_col).strip().lower() == "x":
            continue

        print(f"Processing row {row}: '{employee_name}'")
        roster.employees_processed += 1

        entries: list[RosterEntry] = []

        for col in range(start_day_col, layout.last_day_col + 1):
            if col == layout.spacer_col:
                continue

            cell_text = workbook.get_cell_text(row, col).strip()
            if not cell_text or cell_text in config.IGNORED_CELL_VALUES:
                continue

            date_str = date_cell_to_iso(workbook.get_cell_text(layout.date_row, col))
            entry = parse_cell(employee_name, date_str, cell_text)

            if entry:
                entries.append(entry)
            else:
                print(f"Skipping unknown cell content: {cell_text} at row {row}, col {col}")
                roster.unknown_symbols.add(cell_text)

        if entries:
            roster.entries[employee_name] = entries

    roster.entries = dict(sorted(roster.entries.items()))
    return roster
