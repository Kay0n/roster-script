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


def get_xlsx_path() -> str:
    cwd = os.getcwd()
    for file in os.listdir(cwd):
        if file.endswith(".xlsx"):
            return os.path.join(cwd, file)
    return ""



def main():

    USE_PROXY = True
    USE_LOCAL = True
    START_DATE = date(2025, 4, 21)
    END_DATE = date(2025, 5, 18)



    
    gui_manager = GUIManager()
    keyboard_manager = KeyboardManager()
    kronos_driver =  RosterSelenium()

    load_dotenv(override=True)
    user = os.getenv("KRONOS_USERNAME")
    password = os.getenv("KRONOS_PASSWORD")
   
    keyboard_manager.send_tab() # show interaction dialog on gnome

    if USE_LOCAL:
        gui_data = {
                'day_offset': 0,
                'excel_file_path': get_xlsx_path(),
            }
    else:
        gui_data = gui_manager.show_start_gui()
    
    
    workbook: ExcelWorkbook = ExcelWorkbook(gui_data['excel_file_path'], Config().ICU_DEFAULTS["sheet_name"])
    processor = RosterProcessor(gui_data, Config().ICU_DEFAULTS, workbook, gui_manager, keyboard_manager)

    kronos_driver.setup_driver(USE_PROXY, 8080)
    kronos_driver.login(user, password)
    kronos_driver.select_schedule_hyperfind()
    time.sleep(9)
    kronos_driver.select_date(START_DATE, END_DATE)
    time.sleep(3.5)
    # kronos_driver.find_scrollable_container()
    employee_list = kronos_driver.get_all_employee_names()
    print(employee_list)
    print(len(employee_list))


    moves = kronos_driver.generate_moves(workbook, employee_list)
    

    print("Generated Moves")
    _ = input("Press ENTER to replay...")
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







