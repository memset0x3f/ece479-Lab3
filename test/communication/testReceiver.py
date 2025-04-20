import sys
sys.path.append("../..")

import config
from communication import WifiCommReceiver, BluetoothCommReceiver


def testWifi():
    PORT = config.RECEIVER_PORT
    receiver = WifiCommReceiver(PORT)
    while True:
        data = receiver.receive()
        print("Data received successfully.")
        print(data)

def testBT():
    receiver = BluetoothCommReceiver("raspberrypi", 1)
    while True:
        data = receiver.receive()
        print("Data received successfully.")
        print(data)

if __name__ == "__main__":
    testBT()