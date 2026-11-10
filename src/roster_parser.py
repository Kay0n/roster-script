"""Reads the roster spreadsheet into Shift / PayCodeShift entries. No browser code here."""

import os
import re
from dataclasses import dataclass, field
from datetime import datetime

import config
from config import SheetLayout
from excel_workbook import ExcelWorkbook
from models import PayCodeShift, RosterEntry, Shift


TIMECODE_REGEX = re.compile(r"^\d{4}-\d{4}$")  # nnnn-nnnn, n = digit
LAST_ROW = 300


@dataclass
class ParseResult:
    entries: dict[str, list[RosterEntry]] = field(default_factory=dict)  # employee name -> entries
    unknown_symbols: set[str] = field(default_factory=set)
    employee_count: int = 0

    @property
    def entry_count(self) -> int:
        return sum(len(e) for e in self.entries.values())

    def print_summary(self, employee_ids: dict[str, int]):
        print("Roster ingestion complete")
        print(f"Processed {self.entry_count} shifts from {self.employee_count} employees")
        print("Unknown Symbols:")
        print(self.unknown_symbols)

        print("Invalid Employees:")
        for name in self.entries:
            if name not in employee_ids:
                print(name)


def load_roster(layout: SheetLayout, day_offset: int = 0) -> ParseResult:
    workbook = ExcelWorkbook(find_xlsx_path(), layout.sheet_name)
    return parse_roster(workbook, layout, day_offset)


def find_xlsx_path() -> str:
    cwd = os.getcwd()
    for file in os.listdir(cwd):
        if file.endswith(".xlsx"):
            return os.path.join(cwd, file)
    return ""


def parse_date(date: str) -> str:
    date_dt = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
    return date_dt.strftime("%Y-%m-%d")


def parse_shift(employee_name: str, date_str: str, cell_content: str) -> RosterEntry | None:
    if cell_content in config.SHIFT_TIMES:
        return Shift(employee_name, date_str, config.SHIFT_TIMES[cell_content])

    if TIMECODE_REGEX.match(cell_content):
        return Shift(employee_name, date_str, cell_content)

    paycode_split = cell_content.split("/", 1)
    code = paycode_split[0].strip()

    if code in config.PAYCODES:
        if len(paycode_split) == 1 or not paycode_split[1].strip():
            return None

        try:
            hours = float(paycode_split[1])
        except ValueError:
            raise Exception(f"Invalid hours value '{paycode_split[1]}' for paycode '{code}'")

        return PayCodeShift(employee_name, date_str, config.PAYCODES[code], hours)

    return None


def parse_roster(workbook: ExcelWorkbook, layout: SheetLayout, day_offset: int = 0) -> ParseResult:
    result = ParseResult()

    start_day_col = layout.first_day_col + day_offset
    if start_day_col > 22:
        start_day_col += 1  # account for buffer

    for row in range(layout.first_employee_row, LAST_ROW):
        employee_name = workbook.get_cell(row, layout.kronos_name_col).strip()
        if not employee_name:
            continue
        if workbook.get_cell(row, layout.x_check_col).strip().lower() == "x":
            continue

        print(f"Processing row {row}: '{employee_name}'")
        result.employee_count += 1

        shift_list: list[RosterEntry] = []

        for col in range(start_day_col, layout.last_day_col + 1):
            if col == layout.buffer_col:
                continue

            cell_content = workbook.get_cell(row, col).strip()
            if not cell_content or cell_content in config.SKIP_VALUES:
                continue

            date_str = parse_date(workbook.get_cell(layout.date_row, col))
            shift = parse_shift(employee_name, date_str, cell_content)

            if shift:
                shift_list.append(shift)
            else:
                print(f"Skipping unknown cell content: {cell_content} at row {row}, col {col}")
                result.unknown_symbols.add(cell_content)

        if shift_list:
            result.entries[employee_name] = shift_list

    result.entries = dict(sorted(result.entries.items()))
    return result
