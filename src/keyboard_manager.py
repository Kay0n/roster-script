
from pynput.keyboard import Key, Controller, Listener
import time

class KeyboardManager:
    def __init__(self):
        self.keyboard = Controller()
        self.moves = 0
        self.should_stop = False
        self.process_delay = 0.7
        self.listener = Listener(on_press=self.handle_hotkey)


    def enable_hotkeys(self):
        self.listener.start()

    def handle_hotkey(self, key):
        try:
            if key.char == 'j':
                self.moves += 1
                self.keyboard.press(Key.down)
                self.keyboard.release(Key.down)
            elif key.char == 'k':
                self.moves -= 1
                self.keyboard.press(Key.up)
                self.keyboard.release(Key.up)
            elif key.char == 'r':
                self.moves = 0
            elif key.char == 'e':
                self.keyboard.press(Key.down)
                self.keyboard.release(Key.down)
                self.should_stop = True
            elif key.char == 's':
                self.moves = "skip"
                self.should_stop = True
            elif key.char == 'f':
                self.moves = "end"
                self.should_stop = True
            elif key.char == 'w':
                self.moves = "back"
                self.should_stop = True
        except AttributeError:
            pass

    def simulate_moves(self, moveset):
        print(f"processing moves: {moveset}")
        direction = Key.down if moveset > 0 else Key.up
        for _ in range(abs(moveset)):
            self.keyboard.press(direction)
            self.keyboard.release(direction)
            time.sleep(self.process_delay)

    def unhook_hotkeys(self):
        self.listener.stop()
    
    def type(self, str: str):
        self.keyboard.type(str)
    
    def send_tab(self):
        """Sends a Tab key press."""
        self.keyboard.press(Key.tab)
        self.keyboard.release(Key.tab)








