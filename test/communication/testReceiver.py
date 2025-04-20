import sys
sys.path.append("../..")

from communication import WifiCommReceiver
import config

PORT = config.RECEIVER_PORT

def test():
    receiver = WifiCommReceiver(PORT)
    while True:
        data = receiver.receive()
        print("Data received successfully.")
        print(data)

if __name__ == "__main__":
    test()