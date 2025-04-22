# from communication import WifiCommReceiver, BluetoothCommReceiver
import config
import logging
from mouse import Mouse

logger = logging.getLogger(__name__)

class Receiver:
    def __init__(self, comm):
        self.running = True
        self.receiver = comm
        self.mouse = Mouse()

    def start(self):
        while self.running:
            data = self.receiver.receive()
            if data:
                x, y = self.mouse.solve(data["position"][0], data["position"][1])
                self.mouse.move_to(x, y)
                logger.info(f"Mouse moved to: {x}, {y}")

    def stop(self):
        self.running = False
        self.receiver.close()

if __name__ == "__main__":
    logging.basicConfig(filename=config.LOG_FILE, level=config.LOG_LEVEL)

    if config.COMMUNICATION_TYPE == "wifi":
        from communication import WifiCommReceiver
        port = config.RECEIVER_PORT
        comm = WifiCommReceiver(port)
    elif config.COMMUNICATION_TYPE == "bluetooth":
        from communication import BluetoothCommReceiver
        port = config.SENDER_BT_PORT
        comm = BluetoothCommReceiver(config.SENDER_BT_NAME, port)

    receiver = Receiver(comm)
    try:
        receiver.start()
    except KeyboardInterrupt:
        logger.info("Receiver stopped.")