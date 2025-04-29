import pyautogui
import pydirectinput
import threading
import time
from pynput import keyboard
import math

class PC_Controller: 
    def __init__(self, pause=0.01):
        self.screen_width, self.screen_height = pyautogui.size()
        self.center_x = self.screen_width // 2
        self.center_y = self.screen_height // 2
        self.raw_x_min = -1
        self.raw_x_max = 1 
        self.raw_y_min = -1 
        self.raw_y_max = 1
        pyautogui.PAUSE = pause
        pydirectinput.PAUSE = pause
        self.running = True  # 
        self.listener_thread = threading.Thread(target=self.start_listener, daemon=True)
        self.listener_thread.start()

    def start_listener(self):
        def on_press(key):
            try:
                if key.char == 'q':  #
                    print("[Listener] 'q' pressed. Stopping movement.")
                    self.running = False
                if key.char == 'e':  
                    print("[Listener] 'e' pressed. Resuming movement.")
                    self.running = True
            except AttributeError:
                if key == keyboard.Key.esc:
                    print("[Listener] ESC pressed. Exiting program.")
                    self.running = False
                    exit(0)

        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()

    def solve(self, x, y):
        x_ratio = (x - self.raw_x_min) / (self.raw_x_max - self.raw_x_min)
        y_ratio = (y - self.raw_y_min) / (self.raw_y_max - self.raw_y_min)
        x_screen = int(x_ratio * self.screen_width)
        y_screen = int(y_ratio * self.screen_height)
        x_screen = min(max(x_screen, 5), self.screen_width - 5)
        y_screen = min(max(y_screen, 5), self.screen_height - 5)
        print(f"solved x: {x}, y: {y} to screen x: {x_screen}, y: {y_screen}")
        return x_screen, y_screen
        
    def solve_attitude(self, degree_x, degree_y):
        x_ratio = (degree_x - 60)/(60 - (-60))
        y_ratio = (degree_y - 60)/(60 - (-60))
        x_screen = int(x_ratio * self.screen_width)
        y_screen = int(y_ratio * self.screen_height)
        x_screen = min(max(x_screen, 5), self.screen_width - 5)
        y_screen = min(max(y_screen, 5), self.screen_height - 5)
        return x_screen, y_screen

    def move_to_pydirect(self, x, y):
        if self.running:
            pydirectinput.moveTo(x, y, duration=0.02)
        else:
            print("[move_to_pydirect] Movement paused.")

    def get_position(self):
        x, y = pyautogui.position()
        return x, y
        
    def click(self, x, y):
        if not self.running:
            print("[click] Movement paused.")
            return

        pyautogui.click(x, y)
        
    def move_to(self, x, y):
        if not self.running:
            print("[move_to] Movement paused.")
            return
        pyautogui.moveTo(x, y)

    def double_click(self, x, y):
        if not self.running:
            print("[double_click] Movement paused.")
            return
        pyautogui.doubleClick(x, y)

    def press(self, key):
        if not self.running:
            print("[press] Movement paused.")
            return
        pyautogui.press(key)
def circle(x0, y0, radius, num_points=72):
    points = []
    for i in range(num_points):
        angle = 2 * math.pi * i / num_points
        x = int(x0 + radius * math.cos(angle))
        y = int(y0 + radius * math.sin(angle))
        points.append((x, y))
    return points

if __name__ == "__main__":
    mouse = PC_Controller()
    circle = circle(mouse.center_x, mouse.center_y, 200, 360)
    print(len(circle))
    cnt = 0
    # pyautogui.PAUSE = 0.0001
    while True: 
        start_time = time.time()
        x, y = circle[cnt]
        mouse.move_to_pydirect(x, y)
        cnt += 1
        if cnt >= len(circle):
            cnt = 0
        end_time = time.time()
        print(f"Moved to ({x}, {y}) in {end_time - start_time:.6f} seconds")
        # if cnt == 0:
            # mouse.click(x, y)
        # time.sleep(1)