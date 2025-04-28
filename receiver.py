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
                if data["position"]:
                    x, y = self.mouse.solve(data["position"][0], data["position"][1])
                    self.mouse.move_to(x, y)
                if data["leftEvent"]:
                    self.mouse.click(x, y)
                    logger.info(f"Left click at: {x}, {y}")
                if data["rightEvent"]:
                    self.mouse.double_click(x, y)
                    logger.info(f"Right double click at: {x}, {y}")
                
                logger.info(f"Mouse moved to: {x}, {y}")
                logger.info(f"screen size: {self.mouse.screen_width}, {self.mouse.screen_height}")

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