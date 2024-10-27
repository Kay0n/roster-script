# main.py
from config import Config
from gui_manager import GUIManager
from roster_processor import RosterProcessor
from keyboard_manager import KeyboardManager
import pandas as pd
import time

def main():

    gui_manager = GUIManager()
    keyboard_manager = KeyboardManager()
    
    config_data = gui_manager.show_start_gui()
    
    excel = pd.read_excel(config_data['excel_file_path'], sheet_name=config_data['sheet_name'])
    
    processor = RosterProcessor(config_data, excel, gui_manager, keyboard_manager)
    
    print("Starting Recording...")
    recorded_moves = processor.record_movements()
    
    print("Recording Finished")
    print("Replay in 8 seconds")
    keyboard_manager.unhook_hotkeys()
    time.sleep(8)
    
    special_tracker = processor.process_roster(recorded_moves)
    
    print("Replay Finished")
    print("Special values are:")
    for value in special_tracker:
        print(value)
    print("Please check and save")

if __name__ == "__main__":
    main()