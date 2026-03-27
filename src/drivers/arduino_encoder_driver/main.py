import atexit
import json
import os.path
import threading
import time
import argparse
from typing import Dict

from common import *
from cmm_tools.cmm_comms.socket import CmmSocketServer, DEFAULT_SERVER_IP, DEFAULT_SERVER_PORT, DEV, TOPIC, PAYLOAD, ID
from cmm_tools.color_print import print_warn
# from cmm_tools.cmm_comms.cmm_serial.devices.arduino import ARDUINO_UNO, DFROBOT_BEETLE, ARDUINO_MEGA2560

from arduino_encoders import set_debug as arduino_control_debug, EncoderManager, PARAMS_AS5048A

DEBUG = False
arduino_control_debug(DEBUG)

devices: Dict[str, SerialDeviceInfo] = {"uno": ARDUINO_UNO,
                                        "beetle": DFROBOT_BEETLE,
                                        "mega": ARDUINO_MEGA2560,
                                        }

class Driver:
    def __init__(self, config: Dict, encoders=None):
        self._tx_id = 0
        self._running = False

        # retrieve config parameters
        iface = config.get("interface", None)
        server = config.get("server_address", {})
        baudrate = config.get("baud_rate", DEFAULT_BAUDRATE)

        device: SerialDeviceInfo = devices.get(iface, ARDUINO_UNO)
        self.encoder_manager = EncoderManager(encoders=encoders,
                                              baudrate=baudrate,
                                              iface_device=device,
                                              )

        # server_address = DEFAULT_SERVER_ADDRESS
        host = server.get("host", DEFAULT_SERVER_IP) # "localhost")
        port = server.get("port", DEFAULT_SERVER_PORT)  #8100)
        self.socket_manager = CmmSocketServer(server_address=(host, port),
                                              handler_func=self.handle_request,
                                              )

    def handle_request(self, request):
        if not isinstance(request, Dict):
            print("Request not a dict")
            self.socket_manager.send_msg(request)
            return request

        topic = request[TOPIC]
        payload = request[PAYLOAD]
        device = request[DEV]
        if device is None:
            print("Device not specified")
            self.socket_manager.send_msg(request)
            return request

        if DEBUG:
            print(f"COMMAND RECEIVED -> {topic}\t<{payload}>\t{device}")  # DEBUG

        val: Any = None
        connected = self.encoder_manager.is_encoder_connected(device)
        if not connected:
            status = STATUS_MISSING
            topic = TOPIC_REPLY_DEV_STATUS
        else:
            if topic in (TOPIC_CMD, TOPIC_CMD_ENC, TOPIC_CMD_DROPBOX):
                if payload == REQ_GET_ATT:  # get encoder attached status
                    topic = TOPIC_REPLY_ATTACHED  # TOPIC_REPLY_DEV_STATUS
                    status = STATUS_VAL
                    val = "true" if connected else "false"  # 1 if connected else 0
                elif payload == REQ_GET_SERIAL:  # get encoder serial
                    print("GET SERIAL")
                    topic = TOPIC_REPLY_DROPBOX
                    val = self.encoder_manager.get_model_number(device)
                    status = STATUS_VAL
                elif payload == REQ_GET_POS:  # get motor position
                    topic = TOPIC_REPLY_POS
                    val, _ = self.encoder_manager.get_position(device)
                    status = STATUS_VAL
                elif payload == CMD_SET_HOME:  # set motor home position
                    self.encoder_manager.set_home(device)
                    status = STATUS_OK
                elif payload == REQ_GET_HOMED:  # get homed status
                    topic = TOPIC_REPLY_HOMED
                    val = self.encoder_manager.get_homed(device)
                    status = STATUS_VAL
                elif payload == CMD_RESET_HOMED:  # set homed status
                    topic = TOPIC_REPLY_HOMED
                    self.encoder_manager.reset_homed(device)
                    val = self.encoder_manager.get_homed(device)
                    status = STATUS_VAL
                elif len(payload) > LEN_CMD_VALUED:  # valued commands
                    cmd = payload[:LEN_CMD_VALUED]
                    cmd_val = payload[LEN_CMD_VALUED:]
                    status = STATUS_BAD
                else:
                    print_warn(f"UNKNOWN COMMAND: {request}")
                    status = STATUS_BAD
            else:
                print_warn(f"UNKNOWN TOPIC: {request}")
                status = STATUS_BAD
        if status == STATUS_VAL:
            output = f"{val}"
        else:
            output = status

        tx_msg_txt = f"{output}"

        response = {TOPIC: topic,
                    DEV: device,
                    PAYLOAD: tx_msg_txt,
                    ID: self._tx_id
                    }
        self._tx_id += 1
        self.socket_manager.send_msg(response)
        return response

    def stop(self):
        self.encoder_manager.close()
        self.socket_manager.stop()
        self._running = False
        print("Driver stopped.")

    def run(self):

        self._running = True

        # start thread for socket comms
        print("Starting socket thread...")
        socket_thread = threading.Thread(name="SocketRequestThread",
                                         target=self.socket_manager.run,
                                         daemon=True)
        socket_thread.start()

        # ------------ MAIN LOOP ------------
        print("Running driver...")
        while self._running:
            self.encoder_manager.update()
            # NB message handling is done by the socket_manager asynchonously

            time.sleep(0.02)
        self.stop()


def load_config(filepath: str) -> dict:
    fullpath = os.path.abspath(filepath)
    print(f"Loading config from '{fullpath}'")
    with open(fullpath, "r") as cfg_file:
        config = json.load(cfg_file)
        return config


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Arduino Encoder Driver")
    parser.add_argument("--config", required=True, help="Path to the configuration JSON file")
    args = parser.parse_args()
    CONFIG_FILE = args.config

    cfg = load_config(CONFIG_FILE)

    # (AXIS_ID, {ENCODER RESOLUTION CPR, RPM SCALE FACTOR})
    microtome_encoders = {DEV_KNIFE: (0, PARAMS_AS5048A),
                          DEV_ROT: (1, PARAMS_AS5048A),
                          DEV_TILT: (2, PARAMS_AS5048A),
                          }

    driver = Driver(config=cfg,
                    encoders=microtome_encoders,
                    )

    atexit.register(driver.stop)
    driver.run()
