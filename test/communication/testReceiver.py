import sys
sys.path.append("../..")

from communication import WifiCommReceiver

PORT = 12345

def test():
    sender = WifiCommReceiver(PORT)
    data = sender.receive()
    print("Data received successfully.")
    print(data)

if __name__ == "__main__":
    test()