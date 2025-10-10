from openpyxl import load_workbook
from openpyxl.styles import PatternFill
from typing import Any
from openpyxl.worksheet.worksheet import Worksheet

class ExcelWorkbook:
    def __init__(self, file_path: str, sheet_name: str) -> None:
        self.file_path: str = file_path
        self.workbook = load_workbook(filename=self.file_path)
        self.sheet: Worksheet = self.workbook[sheet_name]


    def get_cell(self, row: int, col: int) -> str:
        return str(self.sheet.cell(row=row, column=col).value or "")


    def set_cell(self, row: int, col: int, value: Any) -> None:
        cell = self.sheet.cell(row=row, column=col)
        cell.value = value
        
        
    def highlight_cell(self, row: int, col: int, hex_color: str = "#FF0000") -> None:
        fill_color =  hex_color.replace('#', '')
        fill_pattern = PatternFill(
            start_color=fill_color,
            end_color=fill_color,
            fill_type="solid"
        )
        self.sheet.cell(row=row, column=col).fill = fill_pattern
    

    def get_highlight_theme(self, row: int, col: int) -> int:
        cell = self.sheet.cell(row=row, column=col)
        if cell.fill and cell.fill.start_color and cell.fill.start_color.type == 'theme' and cell.fill.start_color.theme is not None: # type: ignore
            return cell.fill.start_color.theme # type: ignore
        return 0
 

    def save(self) -> None:
        """Save the workbook."""
        self.workbook.save(self.file_path)
