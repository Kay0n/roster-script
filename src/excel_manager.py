from openpyxl import load_workbook
from openpyxl.styles import PatternFill


class ExcelWorkbook:
    def __init__(self, file_path, sheet_name):
        self.file_path = file_path
        self.workbook = load_workbook(filename=file_path)
        self.sheet = self.workbook[sheet_name]

    def get_cell(self, row: int, col: int) -> str:
        return str(self.sheet.cell(row=row, column=col).value or "")

    def set_cell(self, row: int, col: int, value: any) -> None:
        cell = self.sheet.cell(row=row, column=col)
        cell.value = value
        
        
    def highlight_cell(self, row: int, col: int, hex_color: str = "#FF0000") -> None:
        """
        Highlights a specific cell with the specified color.
        
        Args:
            row (int): Row number (1-based)
            col (int): Column number (1-based)
            color (str): Hex color code (default is red "#FF0000")
        """
        fill_color =  hex_color.replace('#', '')
        fill_pattern = PatternFill(
            start_color=fill_color,
            end_color=fill_color,
            fill_type="solid"
        )
        self.sheet.cell(row=row, column=col).fill = fill_pattern
    
    def get_highlight_theme(self, row: int, col: int) -> int:
        cell = self.sheet.cell(row=row, column=col)
        if cell.fill and cell.fill.start_color and cell.fill.start_color.type == 'theme':
            return cell.fill.start_color.theme
        return 0
 
    
    def save(self):
        """Save the workbook."""
        self.workbook.save(self.file_path)


