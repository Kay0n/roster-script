# roster_processor.py
import time
import keyboard
from keyboard_manager import KeyboardManager
from gui_manager import GUIManager
from excel_manager import ExcelWorkbook
from config import Config
import pynput
from pynput.keyboard import Key


def simulate_moves(self, moveset):
    print("processing moves")
    direction = Key.down if moveset > 0 else Key.up
    for _ in range(abs(moveset)):
        self.keyboard.press(direction)
        self.keyboard.release(direction)
        time.sleep(self.process_delay)

class RosterProcessor:
    def __init__(self, gui_data, excel_settings, excel_workbook, gui_manager, keyboard_manager):
        self.gui_data = gui_data
        self.workbook: ExcelWorkbook = excel_workbook
        self.gui_manager: GUIManager = gui_manager
        self.keyboard_manager: KeyboardManager = keyboard_manager
        self.config: Config = Config()
        self.excel_settings = excel_settings



    def record_movements(self) -> list[int | str]:
        movement_array = []
        current_row = self.excel_settings['first_employee_row']
        self.keyboard_manager.enable_hotkeys()

        while True:
            gui_instance = self.gui_manager.show_name_gui(
                self.workbook.get_cell(current_row, self.excel_settings['name_col']),
                current_row,
                self.excel_settings['name_col']
            )

            self.keyboard_manager.moves = 0
            prev_moves = 0
            self.keyboard_manager.should_stop = False
            
            while not self.keyboard_manager.should_stop:
                time.sleep(0.05)
                if self.keyboard_manager.moves != prev_moves:
                    gui_instance.update_moves(self.keyboard_manager.moves)
                    prev_moves = self.keyboard_manager.moves
            
            moves = self.keyboard_manager.moves
            print(moves)

            if gui_instance.winfo_exists():
                gui_instance.destroy()
            
            if moves == "end":
                break

            if moves == "back":
                current_row -= 1
                continue

            movement_array.append(moves)
            current_row += 1

        return movement_array
    
    def proccess_selenium_roster(self, movement_array) -> set:
        special_tracker = set()

        for row, move in movement_array:
            if move == "skip":
                continue

            simulate_moves(move)

            for col in range(self.excel_settings['first_day_col'], self.excel_settings['last_day_col']):
                
                if col <= self.excel_settings['first_day_col'] + self.gui_data['day_offset']:
                    keyboard.send("tab")
                    time.sleep(0.5)
                    continue

                cell_content = self.workbook.get_cell(row, col)
                if cell_content in self.config.VALUE_DICT:
                    keyboard.write(self.config.VALUE_DICT[cell_content])
                    # DEBUG
                    print(f"""
                        name:{self.excel.iat[row, self.excel_settings['name_col']]}
                        index: {row},{col}
                        value: {self.config.VALUE_DICT[cell_content]}
                    """)

                if cell_content:
                    for val in self.config.SPECIAL_VALUES:
                        if val in cell_content:
                            special_tracker.add(cell_content)

                keyboard.send("tab")
                time.sleep(0.5)

            print("next line")

        return special_tracker



    def process_roster(self, movement_array) -> set:
        special_tracker = set()
        
        for i in range(self.excel_settings['first_employee_row'],
                      self.excel_settings['first_employee_row'] + len(movement_array)):

            moves = movement_array[i - self.excel_settings['first_employee_row']]
            if moves == "skip":
                continue

            self.keyboard_manager.simulate_moves(moves)

            for j in range(self.excel_settings['first_day_col'], self.excel_settings['last_day_col']):
                
                if j <= self.excel_settings['first_day_col'] + self.gui_data['day_offset']:
                    keyboard.send("tab")
                    time.sleep(0.5)
                    continue

                cell_content = self.workbook.get_cell(i, j)
                if cell_content in self.config.VALUE_DICT:
                    keyboard.write(self.config.VALUE_DICT[cell_content])
                    # DEBUG
                    print(f"""
                        name:{self.excel.iat[i, self.excel_settings['name_col']]}
                        index: {i},{j}
                        value: {self.config.VALUE_DICT[cell_content]}
                    """)

                if cell_content:
                    for val in self.config.SPECIAL_VALUES:
                        if val in cell_content:
                            special_tracker.add(cell_content)

                keyboard.send("tab")
                time.sleep(0.5)

            print("next line")

        return special_tracker