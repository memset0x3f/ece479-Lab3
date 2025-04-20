from communication import WifiCommReceiver
from mpu import IMU
import config
import logging

logger = logging.getLogger(__name__)

class Receiver:
    def __init__(self, port):
        self.running = True
        self.receiver = WifiCommReceiver(port)

    def start(self):
        while self.running:
            data = self.receiver.receive()
            if data:
                logger.info(f"Data received: {data}")

    def stop(self):
        self.running = False
        self.receiver.close()

if __name__ == "__main__":
    port = config.RECEIVER_PORT
    logging.basicConfig(level=config.LOG_LEVEL)

    receiver = Receiver(port)
    try:
        receiver.start()
    except KeyboardInterrupt:
        logger.info("Receiver stopped.")