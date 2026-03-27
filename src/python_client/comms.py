from typing import Optional, Tuple

from common import *
from cmm_tools.cmm_comms.socket import CmmSocketClient, DEFAULT_SERVER_IP, DEFAULT_SERVER_PORT, DEV, TOPIC, PAYLOAD, ID


class CommsHandler:
    def __init__(self, server_address: Tuple[str, int] = (DEFAULT_SERVER_IP, DEFAULT_SERVER_PORT)):
        self._running = False
        self._req_queue = []
        self._tx_id = 0

        self._device_driver: CmmSocketClient = CmmSocketClient(server_address=server_address)

    def close(self):
        self._device_driver.disconnect_from_server()

    def connected(self):
        return self._device_driver.is_connected()

    def reconnect(self) -> Tuple[bool, str]:
        return self._device_driver.connect_to_server()

    def get_zeroed(self, axis_name: str) -> bool:
        req = {
            TOPIC: TOPIC_CMD,
            DEV: axis_name,
            PAYLOAD: REQ_GET_HOMED,
        }
        response = self.send_request(req)

        if response and response[TOPIC] == TOPIC_REPLY_HOMED and response[DEV] == axis_name:
            return response[PAYLOAD].lower() == "true"
        return False

    def reset_zeroed(self, axis_name: str) -> bool:
        req = {
            TOPIC: TOPIC_CMD,
            DEV: axis_name,
            PAYLOAD: CMD_RESET_HOMED,
        }
        response = self.send_request(req)

        if response and response[TOPIC] == TOPIC_REPLY_HOMED and response[DEV] == axis_name:
            return response[PAYLOAD].lower() == "false"
        return False

    def get_model(self, axis_name: str) -> Optional[str]:
        #FIXME - parse model from response
        req = {
            TOPIC: TOPIC_CMD,
            DEV: axis_name,
            PAYLOAD: REQ_GET_SERIAL,
        }
        response = self.send_request(req)

        #TEMP
        return "???"

    def get_attached(self, axis_name: str) -> bool:
        req = {
            TOPIC: TOPIC_CMD,
            DEV: axis_name,
            PAYLOAD: REQ_GET_ATT,
        }
        response = self.send_request(req)

        if response and response[TOPIC] == TOPIC_REPLY_ATTACHED and response[DEV] == axis_name:
            return response[PAYLOAD] == "true"
        return False  # TODO should this be False or None?

    def send_request(self, req):
        req[ID] = self._tx_id
        self._tx_id += 1

        resp = self._device_driver.request(req)

        return resp


    def set_zero(self, axis_name: str) -> bool:
        req = {
            TOPIC: TOPIC_CMD,
            DEV: axis_name,
            PAYLOAD: CMD_SET_HOME
        }
        response = self.send_request(req)

        if response and response[TOPIC] == TOPIC_REPLY_ATTACHED and response[DEV] == axis_name:
            return response[PAYLOAD] == STATUS_OK
        return False  # TODO should this be False or None?

    def get_angle(self, axis_name: str) -> Optional[float]:
        req = {
            TOPIC: TOPIC_CMD,
            DEV: axis_name,
            PAYLOAD: REQ_GET_POS
        }
        response = self.send_request(req)

        if response and response[TOPIC] == TOPIC_REPLY_POS and response[DEV] == axis_name:
            angle = response.get(PAYLOAD, None)
            if angle is not None:
                return float(angle)
        return None  # TODO should this be False or None?

    def update(self) -> Optional[str]:

        if not self.connected():
            print("NOT CONNECTED")
            _, status_txt = self.reconnect()
            return status_txt
        return None

    def run(self):
        # # Start listening on incoming socket
        # self.s_in.listen()
        print('Ready for requests')
        self._running = True

        while self._running:
            self.update()
        self.close()
