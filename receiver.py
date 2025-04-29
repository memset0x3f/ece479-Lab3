# from communication import WifiCommReceiver, BluetoothCommReceiver
import config
import logging
from controller import PC_Controller

logger = logging.getLogger(__name__)

class Receiver:
    def __init__(self, comm):
        self.running = True
        self.receiver = comm
        self.controller = PC_Controller()

    def start(self):
        entered = False
        while self.running:
            data = self.receiver.receive()
            if data:
                if data["buttons"]:
                    # logger.info(f"Button states: {data['buttons']}")
                    for button, state in data["buttons"].items():
                        if button == "17":
                            if state == "onclick":
                                self.controller.press("r")
                        if button == "22":
                            if state == "onclick":
                                entered  = not entered
                                if entered:
                                    logger.info("Entered control mode")
                                else:
                                    logger.info("Exited control mode")
                if not entered:
                    continue

                # if data["position"]:
                #     x, y = self.controller.solve(data["position"][0], data["position"][1])
                #     self.controller.move_to(x, y)
                #     logger.info(f"Mouse moved to: {x}, {y}")
                if data["attitude"]:
                    x, y = self.controller.solve_attitude(data["attitude"][0], data["attitude"][2])
                    print(x,y)
                    self.controller.move_to_pydirect(x, y)
                    logger.info(f"Mouse moved to: {x}, {y}")
                if data["leftEvent"]:
                    # self.controller.left_down(x, y)
                    if data["leftEvent"][0] == "single":
                        self.controller.click(x, y)
                    elif data["leftEvent"][0] == "double":
                        self.controller.double_click(x, y)
                    logger.info(f"Left click at: {x}, {y}")
                if data["rightEvent"]:
                    self.controller.right_click(x, y)
                    logger.info(f"Right click at: {x}, {y}")
                    # self.controller.double_click(x, y)
                    # logger.info(f"Right double click at: {x}, {y}")
                
                # logger.info(f"Mouse moved to: {x}, {y}")
                logger.info(f"screen size: {self.controller.screen_width}, {self.controller.screen_height}")

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