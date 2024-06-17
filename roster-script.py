from pynput.keyboard import Key, Controller, Listener
from tkinter import filedialog
import pandas as pd
import time
import tkinter as tk
import winsound
import threading
import ctypes
import keyboard

global gui

winsound.MessageBeep(winsound.MB_OK)
special_tracker = set()
special_tracker_row = set()
# keyboard = Controller()
default_name_column = 6
default_first_employee_row = 3
default_first_day_column = 8
default_last_day_column = default_first_day_column + 28
default_day_offset = 0
default_excel_file_path = "F:/03 Day to Day Information/Rosters/ICU  Rosters-CA/2024/17th June - 14 July 2024.xlsx"
default_sheet_name = "KRONOS"

# Constants
value_dict = {
    "AM": "0645-1900",
    "PM": "1845-0700",
    "E": "0645-1500",
    "L": "1430-2230",
    "N": "2215-0700",
    "ADMIN+4": "0645-1900",
    "ADMIN": "0645-1500",
    "7.5": "0645-1500",
    "7.6": "0645-1535",
    "SKILLS": "1000-1400",
    "CALS": "0645-1500",
    "ALS": "0645-1500",
    "PALS": "0645-1500",
    "1830-2230": "1830-2230"
}
special_values = [
    "AL/",
    "A/L",
    "M/L",
    "ML",
    "MLUP",
    "PHNW",
    "RPH",
    "STUDY",
    "LSL",
    "SD",
    "SL",
]

def waitGUI(special_value):
    def submit():
        gui.quit()
        gui.destroy()
   
    gui = tk.Tk()
    gui.title("Checker GUI")
    label = tk.Label(gui, text=f'''
        Copy and then delete this value: {special_value}
    ''')
    label.pack()
    
    submit_button = tk.Button(gui, text='Submit', command=submit)
    submit_button.pack()
    
    gui.mainloop()


def startGUI():
    def submit():
        global name_column, first_employee_row, first_day_column, last_day_column, day_offset, exel_file_path, sheet_name
        name_column = int(name_col_entry.get()) - 1
        first_employee_row = int(first_row_entry.get()) - 2
        first_day_column = int(first_day_col_entry.get()) - 1
        last_day_column = int(last_day_col_entry.get()) -1
        day_offset = int(day_offset_entry.get())
        exel_file_path = file_path_entry.get()
        sheet_name = sheet_name_entry.get()
        root.quit()
        root.destroy()
    def select_file():
        global exel_file_path
        exel_file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
        file_path_entry.delete(0, tk.END)
        file_path_entry.insert(0, exel_file_path)
   
    root = tk.Tk()
    root.title("Input GUI")
   
    # Define labels
    tk.Label(root, text="Employee Name Column:").grid(row=0)
    tk.Label(root, text="First Employee Row:").grid(row=1)
    tk.Label(root, text="First Day Column:").grid(row=2)
    tk.Label(root, text="Last Day Column:").grid(row=3)
    tk.Label(root, text="Day Offset:").grid(row=4)
    tk.Label(root, text="Excel File Path:").grid(row=5)
    tk.Label(root, text="Sheet Name:").grid(row=6)
   
    name_col_entry = tk.Entry(root)
    first_row_entry = tk.Entry(root)
    first_day_col_entry = tk.Entry(root)
    last_day_col_entry = tk.Entry(root)
    day_offset_entry = tk.Entry(root)
    file_path_entry = tk.Entry(root)
    sheet_name_entry = tk.Entry(root)
   
    name_col_entry.grid(row=0, column=1)
    first_row_entry.grid(row=1, column=1)
    first_day_col_entry.grid(row=2, column=1)
    last_day_col_entry.grid(row=3, column=1)
    day_offset_entry.grid(row=4, column=1)
    file_path_entry.grid(row=5, column=1)
    sheet_name_entry.grid(row=6, column=1)
   
    # Prepopulate fields with default values
    name_col_entry.insert(0, default_name_column)
    first_row_entry.insert(0, default_first_employee_row)
    first_day_col_entry.insert(0, default_first_day_column)
    last_day_col_entry.insert(0, default_last_day_column)
    day_offset_entry.insert(0, default_day_offset)
    file_path_entry.insert(0, default_excel_file_path)
    sheet_name_entry.insert(0, default_sheet_name)
   
    tk.Button(root, text='Select File', command=select_file).grid(row=5, column=2)
    tk.Button(root, text='Submit', command=submit).grid(row=7, column=1, pady=4)
   
    root.mainloop()

def showNameGUI(name_column, current_row, excel):
    employee_name = excel.iat[current_row, name_column]
    gui = tk.Tk()
    gui.title("Checker GUI")
    label = tk.Label(gui, text=f'''
        Name: {employee_name}
        Location: {current_row}, {name_column}
        ~ = pause/unpause
        hjkl = move cell
        e/enter = submit & move on
        s = skip/na
        r = reset
        w = go to previous employee
        f = finish entire recording
    ''')
    label.pack()

    def on_closing():
        gui.quit()
        gui.destroy()

    gui.protocol("WM_DELETE_WINDOW", on_closing)
    gui.attributes('-topmost', True)
    gui.update()

    return gui








def handle_hotkey(key):
    global moves, should_stop

    if key == 'h':
        moves[0] += 1
        keyboard.send('left')
    elif key == 'j':
        moves[1] += 1
        keyboard.send('down')
    elif key == 'k':
        moves[2] += 1
        keyboard.send('up')
    elif key == 'l':
        moves[3] += 1
        keyboard.send('right')
    elif key == 'e':
        keyboard.send('down')
        should_stop = True
    elif key == 's':
        moves[0] = "skip"
        should_stop = True
    elif key == 'r':
        moves = [0, 0, 0, 0]
    elif key == 'f':
        moves[0] = "end"
        should_stop = True





def processMoves(moveset, day_offset):
    for _ in range(moveset[0]):
        keyboard.send("left")
        time.sleep(0.2)
    for _ in range(moveset[1]):
        keyboard.send("down")
        time.sleep(0.2)
    for _ in range(moveset[2]):
        keyboard.send("up")
        time.sleep(0.2)
    for _ in range(moveset[3]):
        keyboard.send("right")
        time.sleep(0.2)
    for _ in range(day_offset):
        keyboard.send("right")
        time.sleep(0.2)
waitGUI("aaaas")
startGUI()
excel = pd.read_excel(exel_file_path, sheet_name=sheet_name)

# for row in range(0, 100):
#     for col in range(0, default_last_day_column):
#         cell_value = excel.iat[row, col]
#         print(f'Row {row + 1}, Column {col + 1}: {cell_value}')
#     print("\n")

# print(len(excel))

current_row = first_employee_row
movement_array = []

keyboard.add_hotkey('h', lambda: handle_hotkey('h'), suppress=True)
keyboard.add_hotkey('j', lambda: handle_hotkey('j'), suppress=True)
keyboard.add_hotkey('k', lambda: handle_hotkey('k'), suppress=True)
keyboard.add_hotkey('l', lambda: handle_hotkey('l'), suppress=True)
keyboard.add_hotkey('e', lambda: handle_hotkey('e'), suppress=True)
keyboard.add_hotkey('s', lambda: handle_hotkey('s'), suppress=True)
keyboard.add_hotkey('r', lambda: handle_hotkey('r'), suppress=True)
keyboard.add_hotkey('f', lambda: handle_hotkey('f'), suppress=True)

while True:
    gui_instance = showNameGUI(name_column, current_row, excel)
    moves = [0, 0, 0, 0]
    should_stop = False
    print("Waiting for hotkeys (h,j,k,l,e,s,r,f)... Press 'e' or 'f' to stop.")
    while not should_stop:
        time.sleep(0.1)
    
    # Close the GUI window when continuing the loop
    if gui_instance.winfo_exists():
        gui_instance.destroy()
    
    if moves[0] == "end":
        break
    movement_array.append(moves)
    current_row += 1

keyboard.unhook_all_hotkeys()

time.sleep(3)
print(len(movement_array))

for i in range(first_employee_row, first_employee_row + len(movement_array) - 1):

    moveset = movement_array[i - first_employee_row]
    if moveset[0] == "skip":
        continue
    processMoves(moveset, day_offset)

    for j in range(first_day_column - day_offset, last_day_column):
        cell_content = str(excel.iat[i, j])
        if cell_content in value_dict:
            keyboard.write(value_dict[cell_content])
            print(f"name:{excel.iat[i, name_column]}, value: {value_dict[cell_content]}")

        if(cell_content):
            for val in special_values:
                if(val in cell_content):
                    special_tracker.add(cell_content)
                    special_tracker_row.add(i)

        keyboard.send("tab")
        time.sleep(0.5)
        
    print("next line")






# for special_val in special_tracker:


#     waitGUI(special_val)
#     time.sleep(4)

#     for i in range(first_employee_row, first_employee_row + len(movement_array) - 1):

#         moveset = movement_array[i - first_employee_row]
#         if moveset[0] == "skip":
#             continue
#         processMoves(moveset, day_offset)

#         if(i not in special_tracker_row):
#             continue
        

#         for j in range(first_day_column - day_offset, last_day_column):
#             cell_content = excel.iat[i, j]
#             if(cell_content == special_val):
#                 keyboard.send('ctrl+v')
#                 print(f"name:{excel.iat[i, name_column]}, value: copypaste")
#                 keyboard.send("tab")
#                 time.sleep(1.5)
#             else:
#                 keyboard.send("tab")
#                 time.sleep(0.5)
            
#         print("next line")

print("FINISHED, please save")
