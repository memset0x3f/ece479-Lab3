import json
import time
import subprocess
import logging
import select

try:
    import bluetooth
except ImportError:
    print("Bluetooth library not found. Make sure to install pybluez.")

import struct   

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

    def wait_for_connection(self):
        self.sock.listen(1)
        self.client_sock, self.client_address = self.sock.accept()

    def send(self, data):
        try:
            data["timestamp"] = time.time()
            json_data = json.dumps(data).encode()
        
            header = struct.pack('!I', len(json_data))
            # send header + payload
            self.client_sock.sendall(header + json_data)
            print(f"Sent {len(json_data)} bytes (plus 4-byte header)")
        except Exception as e:
            print(f"Error sending data: {e}")

    def close(self):
        if self.client_sock:
            self.client_sock.close()
        self.sock.close()


class BluetoothCommReceiver:
    HEADER_SIZE = 4  

    def __init__(self, sender_name, port):
        self.sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        devices = bluetooth.discover_devices(duration=3, lookup_names=True)
        for addr, name in devices:
            if sender_name in name:
                self.sock.connect((addr, port))
                print(f"Connected to {name} at {addr}")
                break
        else:
            raise bluetooth.BluetoothError(f"Device {sender_name} not found.")

    def _recv_exact(self, num_bytes):
        """Helper to read exactly num_bytes or raise if connection closes."""
        buf = b''
        while len(buf) < num_bytes:
            chunk = self.sock.recv(num_bytes - len(buf))
            if not chunk:
                raise bluetooth.BluetoothError("Connection closed unexpectedly")
            buf += chunk
        return buf

    def receive(self):
        
        raw_header = self._recv_exact(self.HEADER_SIZE)
        msg_len = struct.unpack('!I', raw_header)[0]
    
        raw_body = self._recv_exact(msg_len)
        data_dict = json.loads(raw_body.decode())
        assert "timestamp" in data_dict, "Timestamp not found in data"
        return data_dict

    def close(self):
        self.sock.close()
