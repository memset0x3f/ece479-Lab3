import RPi.GPIO as GPIO
import time
from enum import Enum

class KeyState():
    PRESSED = "pressed"
    RELEASED = "released"
    OnClick = "onclick"
    OnRelease = "onrelease"

class ButtonDetector:
    def __init__(self, buttons_addr: list):
        self.n_keys = len(buttons_addr)
        self.button_addr = buttons_addr
        self.addr2button = {x:i for i, x in enumerate(buttons_addr)}
        self.KeyState = KeyState()
        print(self.KeyState)
        self.key_states = {x:self.KeyState.RELEASED for x in buttons_addr}

        GPIO.setmode(GPIO.BCM)
        for key in buttons_addr:
            GPIO.setup(key ,GPIO.IN, GPIO.PUD_UP)
        

    def detectKey(self, key):
        if GPIO.input(key) == 0:
            if(self.key_states[key] == self.KeyState.RELEASED):
                # print(f"KEY {self.addr2button[key]} PRESS") 
                self.key_states[key] = self.KeyState.OnClick
            else:
                self.key_states[key] = self.KeyState.PRESSED
            # self.key_states[key] = KeyState.PRESSED
        else:
            if(self.key_states[key] == self.KeyState.PRESSED):
                # print(f"KEY {self.addr2button[key]} RELEASE") 
                self.key_states[key] = self.KeyState.OnRelease
            else:
                self.key_states[key] = self.KeyState.RELEASED
        
        
            # self.key_states[key] = KeyState.RELEASED
    
    def detectAll(self):
        for key in self.button_addr:
            self.detectKey(key)
        return self.key_states

    def detect(self):                    
        while True:                     
            time.sleep(0.05)
            # print(self.key_states)
            for key in self.button_addr:
                self.detectKey(key)



    