from communication import WifiCommSender, BluetoothCommSender
from mpu import IMU
import config
import logging

logger = logging.getLogger(__name__)

class Sender:
    def __init__(self, comm):
        self.running = True
        self.sender = comm
        self.imu = IMU()

    def start(self):
        while self.running:
            data = self.imu.get_data()
            if data:
                self.sender.send(data)
                logger.info(f"Data sent: {data}")

    def stop(self):
        self.running = False
        self.sender.close()


if __name__ == "__main__":
    logging.basicConfig(filename=config.LOG_FILE, level=config.LOG_LEVEL)

    if config.COMMUNICATION_TYPE == "wifi":
        receiver_ip = config.RECEIVER_IP
        receiver_port = config.RECEIVER_PORT
        comm = WifiCommSender(receiver_ip, receiver_port)
    elif config.COMMUNICATION_TYPE == "bluetooth":
        port = config.SENDER_BT_PORT
        comm = BluetoothCommSender(port)

    sender = Sender(comm)
    try:
        logger.info("Sender started. Press Ctrl+C to stop.")
        sender.start()
    except KeyboardInterrupt:
        logger.info("Sender stopped.")