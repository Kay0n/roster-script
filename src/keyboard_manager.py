# keyboard_manager.py
import keyboard
import time

# class KeyboardManager:
#     def __init__(self):
#         self.moves = 0
#         self.should_stop = False
#         self.process_delay = 0.7


#     def enable_hotkeys(self):
#         keyboard.add_hotkey('j', lambda: self.handle_hotkey('j'), suppress=True)
#         keyboard.add_hotkey('k', lambda: self.handle_hotkey('k'), suppress=True)
#         keyboard.add_hotkey('e', lambda: self.handle_hotkey('e'), suppress=True)
#         keyboard.add_hotkey('s', lambda: self.handle_hotkey('s'), suppress=True)
#         keyboard.add_hotkey('r', lambda: self.handle_hotkey('r'), suppress=True)
#         keyboard.add_hotkey('f', lambda: self.handle_hotkey('f'), suppress=True)


#     def handle_hotkey(self, key):
#         if key == 'j':
#             self.moves += 1
#             keyboard.send('down')
#         elif key == 'k':
#             self.moves -= 1
#             keyboard.send('up')
#         elif key == 'r':
#             self.moves = 0
#         elif key == 'e':
#             keyboard.send('down')
#             self.should_stop = True
#         elif key == 's':
#             self.moves = "skip"
#             self.should_stop = True
#         elif key == 'f':
#             self.moves = "end"
#             self.should_stop = True
#         elif key == 'w':
#             self.moves = "back"
#             self.should_stop = True
        

#     def simulate_moves(self, moveset):
#         print("processing moves")
#         direction = "down" if moveset > 0 else "up"
#         for _ in range(abs(moveset)):
#             keyboard.send(direction)
#             time.sleep(self.process_delay)


#     def unhook_hotkeys(self):
#         keyboard.unhook_all_hotkeys()