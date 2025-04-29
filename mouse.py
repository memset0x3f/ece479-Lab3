import pyautogui
import math
import time
import logging
import pydirectinput


class PC_Controller: 
    def __init__(self, pause=0.001):
        self.screen_width, self.screen_height = pyautogui.size()
        self.center_x = self.screen_width // 2
        self.center_y = self.screen_height // 2
        self.raw_x_min = -1
        self.raw_x_max = 1 
        self.raw_y_min = -1 
        self.raw_y_max = 1
        # self.MAX_X = 1
        # self.MAX_Y = 1
        pyautogui.PAUSE = pause
        pydirectinput.PAUSE = pause
        # print(self.center_x, self.center_y)
    def solve(self, x, y):
        x_ratio = (x - self.raw_x_min) / (self.raw_x_max - self.raw_x_min)
        y_ratio = (y - self.raw_y_min) / (self.raw_y_max - self.raw_y_min)
        x_screen = int(x_ratio * self.screen_width)
        y_screen = int(y_ratio * self.screen_height)
        # x_ratio, y_ratio = x / self.MAX_X, y / self.MAX_Y
        # x_screen, y_screen = int(x_ratio * self.screen_width/2 + self.center_x), int(y_ratio * self.screen_height/2 + self.center_x)
        # x_screen = min(max(x_screen, 2), self.screen_width - 2)
        # y_screen = min(max(y_screen, 2), self.screen_height - 2)
        # if x_screen < 0:
        #     raise ValueError("x_screen is negative")
        # logging.log(f"solved x: {x}, y: {y} to screen x: {x_screen}, y: {y_screen}")
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
        logging.info(f"solved x: {degree_x}, y: {degree_y} to screen x: {x_screen}, y: {y_screen}")
        return x_screen, y_screen
    
    def move_to_pydirect(self, x,y):
        pydirectinput.moveTo(x, y, duration=0.02)
        # pydirectinput.move(x, y, duration=0.1)


    
    def get_position(self):
        x, y = pyautogui.position()
        return x, y
        
    def click(self, x, y):
        pyautogui.click(x, y)
        
        
    def move_to(self, x, y):
        pyautogui.moveTo(x, y)

    def double_click(self, x, y):
        pyautogui.doubleClick(x, y)

    def press(self, key):
        pyautogui.press(key)

# if __name__ == "__main__":
#     print("Press Ctrl+C to exit")
#     mouse = PC_Controller()
#     while True: 
#         x = int(input("x: "))
#         y = int(input("y: "))
#         x, y = mouse.solve(x, y)
#         print(f"solved x: {x}, y: {y}")
#         mouse.move_to(x, y)
    # mouse.click(x, y)
#make a [(x,y)] of circle in the center of the screen,
#with radius 100
#input (x0, y0) is the center of the circle
#and num of points 
def circle(x0, y0, radius, num_points=72):
    points = []
    for i in range(num_points):
        angle = 2 * math.pi * i / num_points
        x = int(x0 + radius * math.cos(angle))
        y = int(y0 + radius * math.sin(angle))
        points.append((x, y))
    return points


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
    if cnt == 0:
        mouse.click(x, y)
    # time.sleep(1)

    

