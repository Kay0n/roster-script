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

    USE_PROXY = True
    ICU_DEFAULTS = Config().ICU_DEFAULTS
    START_DATE = date(2025, 1, 27)
    END_DATE = date(2025, 2, 23)
    
    gui_manager = GUIManager()
    keyboard_manager = KeyboardManager()
    kronos_driver =  RosterSelenium()

    load_dotenv()
    user = os.getenv("KRONOS_USERNAME")
    password = os.getenv("KRONOS_PASSWORD")
   
    
    keyboard_manager.send_tab() # show interaction dialog on gnome
    gui_data = gui_manager.show_start_gui()
    
    
    workbook: ExcelWorkbook = ExcelWorkbook(gui_data['excel_file_path'], ICU_DEFAULTS["sheet_name"])
    processor = RosterProcessor(gui_data, ICU_DEFAULTS, workbook, gui_manager, keyboard_manager)

    kronos_driver.setup_driver(USE_PROXY, 8080)
    kronos_driver.login(user, password)
    kronos_driver.select_schedule_hyperfind()
    time.sleep(5)
    kronos_driver.select_date(START_DATE, END_DATE)
    time.sleep(3.5)
    # kronos_driver.find_scrollable_container()
    employee_list = kronos_driver.get_all_employee_names()
    print(employee_list)
    print(len(employee_list))

    # print("Starting Recording")
    # _ = input("Press ENTER to continue...")

    moves = kronos_driver.generate_moves(workbook, employee_list)

    for move in moves:
        print(move)
    
    # # print("Starting Recording...")
    # # recorded_moves = processor.record_movements()
    # keyboard_manager.unhook_hotkeys()

    print("Recording Finished")
    _ = input("Press ENTER to continue...")
    print("Replay in 8 seconds")
    time.sleep(8)


    special_tracker = processor.proccess_selenium_roster(moves)


    print("Replay Finished")
    print("Special values are:")
    for value in special_tracker:
        print(value)
    print("Please check and save")

if __name__ == "__main__":
    main()







