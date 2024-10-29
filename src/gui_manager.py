# gui_manager.py
import tkinter as tk
from tkinter import filedialog

class GUIManager:


    def show_start_gui(self) -> tk.Tk:
        def submit():
            nonlocal config_data
            config_data = {
                'day_offset': int(day_offset_entry.get()),
                'excel_file_path': file_path_entry.get(),
            }
            root.quit()
            root.destroy()

        def select_file():
            file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
            file_path_entry.delete(0, tk.END)
            file_path_entry.insert(0, file_path)

        root = tk.Tk()
        root.title("Input GUI")
        config_data = None

        # Create and arrange GUI elements
        labels = ["Day Offset:", "Excel File Path:"]
        
        entries = []
        for i, label in enumerate(labels):
            tk.Label(root, text=label).grid(row=i)
            entry = tk.Entry(root)
            entry.grid(row=i, column=1)
            entries.append(entry)

        [day_offset_entry, file_path_entry] = entries

        from config import Config
        defaults = Config().ICU_DEFAULTS

        
        day_offset_entry.insert(0, defaults['day_offset'])
        file_path_entry.insert(0, defaults['excel_file_path'])

        tk.Button(root, text='Select File', command=select_file).grid(row=5, column=2)
        tk.Button(root, text='Submit', command=submit).grid(row=7, column=1, pady=4)

        root.mainloop()
        return config_data



    def show_name_gui(self, employee_name, current_row, name_column) -> tk.Tk:
        gui = tk.Tk()
        gui.title("Name GUI")

        move_frame = tk.Frame(gui)
        move_frame.pack(pady=10)
        moves_label = tk.Label(move_frame, text="Moves: 0", font=("Arial", 16))
        moves_label.pack(side=tk.LEFT, padx=20)

        
        tk.Label(gui, text=f"Name: {employee_name}", font=("Arial", 40)).pack()
        tk.Label(gui, text=f'''
            Location: {current_row}, {name_column}
            ~ = pause/unpause
            j/k = move cell down/up
            e/enter = submit & move on
            s = skip/na
            r = reset current employee
            w = go to previous employee
            f = finish entire recording
        ''').pack()

        gui.geometry("500x300+100+100")
        gui.attributes('-topmost', True)
        gui.update()

        def update_moves(moves):
            moves_label.config(text=f"Moves: {moves}")
            gui.update()
            
        gui.update_moves = update_moves

        return gui
    


    def update_moves_display(self, gui_instance, moves):
        if gui_instance and gui_instance.winfo_exists():
            gui_instance.moves_label.config(text=f"Moves: {moves}")
            gui_instance.update()



    def show_wait_gui(self, special_value) -> tk.Tk:
        def submit():
            gui.quit()
            gui.destroy()

        gui = tk.Tk()
        gui.title("Checker GUI")
        
        label = tk.Label(gui, text=f'''
            Copy and then delete this value: {special_value}
            Then arrow navigate to the start cell
        ''')
        label.pack()
        
        submit_button = tk.Button(gui, text='Submit', command=submit)
        submit_button.pack()
        
        gui.mainloop()