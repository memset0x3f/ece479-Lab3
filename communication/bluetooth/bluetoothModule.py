import struct
import bluetooth 
import json 
import logging
import select 
import time
class BluetoothCommReceiver:
    HEADER_SIZE = 4  # 4 bytes for a big-endian unsigned int

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
        """Helper to keep calling recv until we have exactly num_bytes."""
        buf = b''
        while len(buf) < num_bytes:
            chunk = self.sock.recv(num_bytes - len(buf))
            if not chunk:
                # connection closed or error
                raise bluetooth.BluetoothError("Connection closed unexpectedly")
            buf += chunk
        return buf

    def receive(self):
        # 1. Read the 4-byte header
        raw_header = self._recv_exact(self.HEADER_SIZE)
        # 2. Unpack it to get message length
        msg_len = struct.unpack('!I', raw_header)[0]
        # 3. Read exactly msg_len bytes
        raw_body = self._recv_exact(msg_len)
        # 4. Decode JSON
        data_dict = json.loads(raw_body.decode())
        assert "timestamp" in data_dict, "Timestamp not found in data"
        return data_dict

    def close(self):
        self.sock.close()
