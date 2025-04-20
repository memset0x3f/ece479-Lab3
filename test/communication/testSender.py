import sys
sys.path.append("../..")

from communication import WifiCommSender
import config

RECEIVER_IP = config.RECEIVER_IP
RECEIVER_PORT = config.RECEIVER_PORT

def test():
    sender = WifiCommSender(RECEIVER_IP, RECEIVER_PORT)
    data = {"message": "Hello, World!"}
    sender.send(data)
    print("Data sent successfully.")

if __name__ == "__main__":
    test()