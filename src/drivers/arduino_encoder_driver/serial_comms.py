from __future__ import annotations

from typing import List

from common import *
from cmm_tools.cmm_comms.cmm_serial import CmmPortHandler, CmmPacketHandler, SerialConfig, TYPE_HEARTBEAT


class SerialInterface:
    """Manages the interface to a serial device or serial network. Handles
    the serial port and packet protocol.
    """
    def __init__(self, port: str = None, baud=DEFAULT_BAUDRATE,
                 device_type: SerialDeviceInfo = None):
        self._port_handler: CmmPortHandler | None = None
        self._packet_handler: CmmPacketHandler | None = None

        assert port is not None or device_type is not None, "Port or device type must be provided"

        self._port_handler = CmmPortHandler(iface_device=device_type, baud=baud, port=port)
        if self._port_handler.open_port():
            print(f"Opened: {self._port_handler.get_port_name()}")

            if self._port_handler.set_baud_rate(baud):
                print(f"Baudrate: {self._port_handler.get_baud_rate()}")
        else:
            print("Failed to open port")

        self._packet_handler = CmmPacketHandler(name="CMM Packet Handler", config=SerialConfig(baud=baud))

    def close(self):
        self._port_handler.close_port()

    def get_param(self, param):
        return self._packet_handler.get_param(param)

    def send_heartbeat(self) -> SerialCommResponse:
        if not self._port_handler.is_open:
            return False, COMM_NOT_AVAILABLE, "Port not open"

        response = self.request(TYPE_HEARTBEAT, data=EMPTY_SEQ, suppress_text=True)
        if not response:
            return False, COMM_RX_FAIL, "No response"

        if response.type == TYPE_HEARTBEAT and response.data == DATA_TRUE:
            return True, COMM_SUCCESS, ""
        return False, COMM_RX_FAIL, f"Unknown RX error: {response}"

    def flush_rx(self):
        self._port_handler.flush_rx_buffer()

    def _validate_response(self, request, response):
        """
        Ensure data from a response is valid for a particular request
        """
        raise NotImplementedError

    def get_last_comm_time(self):
        return self._port_handler.last_comm_time

    def request(self, type: bytes, data: bytes, suppress_text=False, timeout=2) -> Message | None:
        # TODO change this to take a message in?
        msg = Message(data=data, mtype=type)
        msg.serialise()

        # clear out any unread messages
        unreads = self.read_messages(suppress=suppress_text)

        response = self._port_handler.send_request(msg, timeout=timeout)
        return response

    def read_messages(self, suppress=False) -> List[Message]:
        """Reads all available messages in serial buffer and parses them"""
        msgs = self._port_handler.parse_all_messages()

        if not suppress:
            if len(msgs) > 0:
                print(f"Received {len(msgs)} messages")
                for msg in msgs:
                    print("\t", msg)
        return msgs
