import json
import time
import subprocess
import bluetooth
import logging
import select

class BluetoothCommSender:
    def _getMAC(self):
        result = subprocess.run(["hciconfig"], capture_output=True, text=True)
        output = result.stdout
        for line in output.splitlines():
            if "BD Address" in line:
                parts = line.strip().split()
                idx = parts.index("Address:") + 1
                return parts[idx]
        return None

    def __init__(self, port):
        # self.mac = self._getMAC()
        self.sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.sock.bind(("", port))
        self.client_sock = None
        self.client_address = None

        self.wait_for_connection()
        # data = self.client_sock.recv(10)  # Receive data to establish connection
        # print(f"Received data: {data}")

    def wait_for_connection(self):
        self.sock.listen(1)
        self.client_sock, self.client_address = self.sock.accept()
        print(f"Connected to {self.client_address}")


    def send(self, data):
        try:
            data["timestamp"] = time.time()
            json_data = json.dumps(data)
            self.client_sock.send(json_data.encode())
        except Exception as e:
            print(f"Error sending data: {e}")

    def close(self):
        if self.client_sock:
            self.client_sock.close()
        self.sock.close()

class BluetoothCommReceiver:
    def __init__(self, sender_name, port):
        self.sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        devices = bluetooth.discover_devices(duration=3, lookup_names=True)
        for addr, name in devices:
            if sender_name in name:
                self.sock.connect((addr, port))
                print(f"Connected to {name} at {addr}")
                break
        else:
            print(f"Device {sender_name} not found.")
            return

    def receive(self):
        data = self.sock.recv(1024)
        if not data:
            raise bluetooth.BluetoothError("Connection closed.")
        data_dict = json.loads(data.decode())
        assert "timestamp" in data_dict, "Timestamp not found in data"
        return data_dict

    def close(self):
        self.sock.close()