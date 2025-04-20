from communication import WifiCommSender
from mpu import IMU
import config
import logging

logger = logging.getLogger(__name__)

class Sender:
    def __init__(self, receiver_ip, receiver_port):
        self.running = True
        self.sender = WifiCommSender(receiver_ip, receiver_port)
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
    receiver_ip = config.RECEIVER_IP
    receiver_port = config.RECEIVER_PORT
    logging.basicConfig(level=config.LOG_LEVEL)

    sender = Sender(receiver_ip, receiver_port)
    try:
        logger.info("Sender started. Press Ctrl+C to stop.")
        sender.start()
    except KeyboardInterrupt:
        logger.info("Sender stopped.")