import logging

LOG_LEVEL = logging.INFO
LOG_FILE = None

COMMUNICATION_TYPE = "bluetooth"  # Options: "bluetooth", "wifi"

RECEIVER_IP = "192.168.137.130"
RECEIVER_PORT = 12345

SENDER_BT_NAME = "raspberrypi"
SENDER_BT_PORT = 1

BUTTONS_ADDR = [17, 27, 22, 23]

SETTINGS_FILE = "mpu/RTIMULib"