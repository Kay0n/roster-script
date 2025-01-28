# roster_processor.py
import time
from keyboard_manager import KeyboardManager
from gui_manager import GUIManager
from excel_manager import ExcelWorkbook
from config import Config



class RosterProcessor:
    def __init__(self, gui_data, excel_settings, excel_workbook, gui_manager, keyboard_manager):
        self.gui_data = gui_data
        self.workbook: ExcelWorkbook = excel_workbook
        self.gui_manager: GUIManager = gui_manager
        self.keyboard: KeyboardManager = keyboard_manager
        self.config: Config = Config()
        self.excel_settings = excel_settings



    def record_movements(self) -> list[int | str]:
        movement_array = []
        current_row = self.excel_settings['first_employee_row']
        self.keyboard.enable_hotkeys()

        while True:
            gui_instance = self.gui_manager.show_name_gui(
                self.workbook.get_cell(current_row, self.excel_settings['name_col']),
                current_row,
                self.excel_settings['name_col']
            )

            self.keyboard.moves = 0
            prev_moves = 0
            self.keyboard.should_stop = False
            
            while not self.keyboard.should_stop:
                time.sleep(0.05)
                if self.keyboard.moves != prev_moves:
                    gui_instance.update_moves(self.keyboard_manager.moves)
                    prev_moves = self.keyboard.moves
            
            moves = self.keyboard.moves
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
        tab_delay = 0.6

        day_offset = self.excel_settings['first_day_col'] + self.gui_data['day_offset']
        if day_offset > 22: day_offset += 1


        for row, move in movement_array:
            if move == "skip":
                continue

            self.keyboard.simulate_moves(move)

            # range (8, 36 + 1) to be inclusive
            for col in range(self.excel_settings['first_day_col'], self.excel_settings['last_day_col'] + 1):
                print(f"{self.workbook.get_cell(row, self.excel_settings['name_col'])}: {row},{col}")

                if col == 22: # skip middle column
                    print("MIDDLE SKIP")
                    continue


                if col < day_offset: # skip day offset

                    print("OFFSET SKIP")
                    self.keyboard.send_tab()

                    if col < self.excel_settings['first_day_col'] + 13: time.sleep(0.35) 
                    else: time.sleep(tab_delay)

                    continue

                


                cell_content = self.workbook.get_cell(row, col)
                print(cell_content)
                if cell_content and cell_content in self.config.VALUE_DICT:
                    print(f"typing: {self.config.VALUE_DICT[cell_content]}")
                    self.keyboard.type(self.config.VALUE_DICT[cell_content])
                if cell_content:
                    for val in self.config.SPECIAL_VALUES:
                        if val in cell_content:
                            special_tracker.add(cell_content)

                self.keyboard.send_tab() 
                time.sleep(tab_delay)

        return special_tracker

