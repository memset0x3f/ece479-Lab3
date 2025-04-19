import socket
import json
import time


class WifiCommSender:
    def __init__(self, reciever_ip, reciever_port):
        self.reciever_ip = reciever_ip
        self.reciever_port = reciever_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send(self, data):
        try:
            data["timestamp"] = time.time()
            json_data = json.dumps(data)
            self.sock.sendto(json_data.encode(), (self.reciever_ip, self.reciever_port))
        except Exception as e:
            print(f"Error sending data: {e}")

class WifiCommReceiver:
    def __init__(self, port):
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("", self.port))
        self.server_timestamp = None

    def receive(self):
        try:
            while True:
                data, addr = self.sock.recvfrom(1024)
                data_dict = json.loads(data.decode())
                assert "timestamp" in data_dict, "Timestamp not found in data"
                if self.server_timestamp is None or data_dict["timestamp"] > self.server_timestamp:
                    self.server_timestamp = data_dict["timestamp"]
                    return data_dict
            
        except Exception as e:
            print(f"Error receiving data: {e}")
            return None

