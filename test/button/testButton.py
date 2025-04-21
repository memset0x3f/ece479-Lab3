import sys
sys.path.append("../..")

from button import ButtonDetector
import config

b = ButtonDetector(config.BUTTONS_ADDR)
b.detect()
