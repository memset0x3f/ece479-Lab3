import sys
sys.path.append("../..")

from comm import WifiCommSender

RECEIVER_IP = "localhost"
RECEIVER_PORT = 12345

def test():
    sender = WifiCommSender(RECEIVER_IP, RECEIVER_PORT)
    data = {"message": "Hello, World!"}
    sender.send(data)
    print("Data sent successfully.")

if __name__ == "__main__":
    test()