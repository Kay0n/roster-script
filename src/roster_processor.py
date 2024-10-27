# roster_processor.py
import time
import keyboard
from keyboard_manager import KeyboardManager
from gui_manager import GUIManager
from config import Config

class RosterProcessor:
    def __init__(self, config_data, excel, gui_manager, keyboard_manager):
        self.config_data = config_data
        self.excel = excel
        self.gui_manager: GUIManager = gui_manager
        self.keyboard_manager: KeyboardManager = keyboard_manager
        self.config: Config = Config()



    def record_movements(self) -> list[int | str]:
        movement_array = []
        current_row = self.config_data['first_employee_row']
        self.keyboard_manager.enable_hotkeys()

        while True:
            gui_instance = self.gui_manager.show_name_gui(
                self.excel.iat[current_row, self.config_data['name_column']],
                current_row,
                self.config_data['name_column']
            )

            self.keyboard_manager.moves = 0
            self.keyboard_manager.should_stop = False
            
            while not self.keyboard_manager.should_stop:
                time.sleep(0.05)
                gui_instance.update_moves(self.keyboard_manager.moves)
            
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
    


    def process_roster(self, movement_array) -> set:
        special_tracker = set()
        
        for i in range(self.config_data['first_employee_row'],
                      self.config_data['first_employee_row'] + len(movement_array)):

            moves = movement_array[i - self.config_data['first_employee_row']]
            if moves == "skip":
                continue

            self.keyboard_manager.simulate_moves(moves)

            for j in range(self.config_data['first_day_column'],
                         self.config_data['last_day_column']):
                
                if j <= self.config_data['first_day_column'] + self.config_data['day_offset']:
                    keyboard.send("tab")
                    time.sleep(0.5)
                    continue

                cell_content = str(self.excel.iat[i, j])
                if cell_content in self.config.VALUE_DICT:
                    keyboard.write(self.config.VALUE_DICT[cell_content])
                    print(f"({i},{j}) name:{self.excel.iat[i, self.config_data['name_column']]}, "
                          f"value: {self.config.VALUE_DICT[cell_content]}")

                if cell_content:
                    for val in self.config.SPECIAL_VALUES:
                        if val in cell_content:
                            special_tracker.add(cell_content)

                keyboard.send("tab")
                time.sleep(0.5)

            print("next line")

        return special_tracker