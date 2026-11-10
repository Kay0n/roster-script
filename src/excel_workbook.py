from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet


class ExcelWorkbook:
    def __init__(self, file_path: str, sheet_name: str) -> None:
        self.file_path = file_path
        self.workbook = load_workbook(filename=file_path, data_only=True)
        self.sheet: Worksheet = self.workbook[sheet_name]

    def get_cell_text(self, row: int, col: int) -> str:
        return str(self.sheet.cell(row=row, column=col).value or "")
