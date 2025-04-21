import pyautogui
import math
import time



class Mouse: 
    def __init__(self, pause=0.0001):
        self.screen_width, self.screen_height = pyautogui.size()
        self.center_x = self.screen_width // 2
        self.center_y = self.screen_height // 2
        pyautogui.PAUSE = pause
        
    def solve(self, x, y):
        #x,y is the position estimated by the mpu
        #solve the position to the screen; 
        pass
        
    
    def get_position(self):
        x, y = pyautogui.position()
        return x, y
        
    def click(self, x, y):
        pyautogui.click(x, y)
        
    def move_to(self, x, y):
        pyautogui.moveTo(x, y)


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


mouse = Mouse()
circle = circle(mouse.center_x, mouse.center_y, 200, 360)
print(len(circle))
cnt = 0
# pyautogui.PAUSE = 0.0001
while True: 
    
    start_time = time.time()
    x, y = circle[cnt]
    mouse.move_to(x, y)
    cnt += 1
    if cnt >= len(circle):
        cnt = 0
    end_time = time.time()
    print(f"Moved to ({x}, {y}) in {end_time - start_time:.6f} seconds")
    # if cnt == 0:
        # mouse.click(x, y)
    # time.sleep(0.0001)

    

