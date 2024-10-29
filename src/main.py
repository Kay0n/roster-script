# main.py
from dotenv import load_dotenv
from config import Config
from gui_manager import GUIManager
from roster_processor import RosterProcessor
from keyboard_manager import KeyboardManager
from excel_manager import ExcelWorkbook
from kronos_driver import RosterSelenium
from datetime import date
import time
import os


def main():

    ICU_DEFAULTS = Config().ICU_DEFAULTS
    gui_manager = GUIManager()
    keyboard_manager = KeyboardManager()
    load_dotenv()
    user = os.getenv("KRONOS_USERNAME")
    password = os.getenv("KRONOS_PASSWORD")
    kronos_driver =  RosterSelenium()
    
    gui_data = gui_manager.show_start_gui()
    
    workbook: ExcelWorkbook = ExcelWorkbook(gui_data['excel_file_path'], ICU_DEFAULTS["sheet_name"])
    processor = RosterProcessor(gui_data, ICU_DEFAULTS, workbook, gui_manager, keyboard_manager)

    kronos_driver.setup_driver()
    kronos_driver.login(user, password)
    kronos_driver.select_schedule_hyperfind()
    time.sleep(2)
    kronos_driver.select_date(date(2024, 11, 4), date(2024, 12, 1))
    time.sleep(5)
    # kronos_driver.find_scrollable_container()
    employee_list = kronos_driver.get_all_employee_names()
    print(len(employee_list))

    print("Starting Recording")
    _ = input("Press ENTER to continue...")

    moves = kronos_driver.generate_moves(workbook, employee_list)
    
    # # print("Starting Recording...")
    # # recorded_moves = processor.record_movements()
    # keyboard_manager.unhook_hotkeys()

    print("Recording Finished")
    _ = input("Press ENTER to continue...")
    print("Replay in 8 seconds")
    time.sleep(8)

    # special_tracker = processor.process_roster(recorded_moves)
    special_tracker = processor.proccess_selenium_roster(moves)
    
    print("Replay Finished")
    print("Special values are:")
    for value in special_tracker:
        print(value)
    print("Please check and save")

if __name__ == "__main__":
    main()







