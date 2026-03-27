"""
UQJTAUFA

For AS5048A encoders using Arduino
"""
from __future__ import annotations

import time
from typing import Dict

from common import *
from cmm_tools.color_print import print_c, Color, set_color
from serial_comms import SerialInterface, COMM_SUCCESS, COMM_NOT_AVAILABLE
from cmm_tools.cmm_comms.cmm_serial.devices.arduino import *
from cmm_tools.cmm_comms.cmm_serial import TYPE_WATCHDOG, TYPE_ERROR, TYPE_DEBUG, TYPE_INFO


# ------ Custom Parameters ------
REBOOT_CHECK_MSG_COUNT = 10  # number msgs before checking reboot status
RESPONSE_FAILED = -3001, 0

DEBUG = False

def set_debug(debug_state: bool):
    global DEBUG
    DEBUG = debug_state

# Encoder errors
ENC_OK = 1
ENC_ERR_UNKNOWN = 0
ENC_ERR_NO_RESPONSE = -1
ENC_ERR_PARITY = -2
ENC_ERR_FRAMING = -3
ENC_ERR_CMD = -4
ENC_ERR_OCF = -5
ENC_ERR_OVF = -6
ENC_ERR_COMP_HIGH = -7
ENC_ERR_COMP_LOW = -8

EncoderErrorTxt = {
    ENC_ERR_NO_RESPONSE: "No response",
    ENC_ERR_PARITY: "Parity error",
    ENC_ERR_FRAMING: "Framing error",
    ENC_ERR_CMD: "Invalid command",
    ENC_ERR_OCF: "Offset compensation not finished",
    ENC_ERR_OVF: "CORDIC overflow",
    ENC_ERR_COMP_HIGH: "Compensation high",
    ENC_ERR_COMP_LOW: "Compensation low",
    ENC_ERR_UNKNOWN: "Unknown error",
}

PARAMS_AS5048A = {K_CPR: 16384}


def _invert_bits(val, nbits=BITSIZE_32):
    max_val = (1 << nbits) - 1
    return max_val - val

def _raw_to_2s_comp(val_raw, nbits=BITSIZE_32):
    """ Converts a value stored in an nbits integer into a 2's comp
    signed representation.
    """
    if val_raw > (2 ** (nbits - 1) - 1):
        val = val_raw - (1 << nbits)
    else:
        val = val_raw
    return val


def _2s_comp_to_raw(val, nbits=BITSIZE_32):
    """ Converts a signed 2s complement value into an integer of length nbits.
    Note: cannot handle values exceeding  +/- 2**(nbits-1)
    """
    # abs_max = 2**nbits - 1
    if val >= 0:
        val_raw = val
    else:
        val_raw = (abs(val) + (1 << nbits))
    # val_raw = abs_max & val_raw  # constrain to be within required bit range
    return val_raw


class Encoder:
    def __init__(self, name: str, enc_id: int, config: Dict,
                 serial_manager=None):
        self._name: str = name
        self._id: int = enc_id
        self._id_byte = enc_id.to_bytes(length=1, byteorder="big", signed=False)
        self._is_connected: bool = False
        self._last_comm_time: float = 0
        self._present_pos_raw = 0
        self._present_pos = 0.0
        self._t_pos = 0
        self._zero_offset = 0  # TEMP?
        self._at_reboot = True
        self._n_msg = 0
        self._is_zeroed = False

        self._dir = DRIVE_DIR_NORMAL

        self._serial_manager = serial_manager

        self._cpr: int = config[K_CPR]  # encoder cpr

    def is_zeroed(self):
        return self._is_zeroed

    def reset_zeroed(self):
        self._is_zeroed = False

    @property
    def name(self):
        return self._name

    @property
    def id(self):
        return self._id

    def is_connected(self) -> bool:
        return self._is_connected

    def _degrees_to_pos(self, deg: float) -> int:
        pos = (deg + self._zero_offset) * self._cpr / DEGREES_PER_REV
        return int(pos)

    def _pos_to_deg(self, pos: int) -> float:
        deg = pos * DEGREES_PER_REV / self._cpr - self._zero_offset
        return deg

    def set_home(self):
        print_c(f"{self._name} - Set zero", Color.cyan)
        data = self._send_request(TYPE_SET_ZERO)
        if data is not None:
            self._is_zeroed = True
            return [int(elem) for elem in data.split(SEP_CHAR)]
        return data

    def get_present_pos(self) -> Tuple[float, int]:
        return self._present_pos, self._t_pos

    def update_position(self) -> float | None:
        """Returns the current angle of the encoder (absolute)"""
        data = self._send_request(TYPE_ANGLE)
        if data is not None:
            dir_mod = -1 if self._dir == DRIVE_DIR_REVERSE else 1
            angle = dir_mod * float(data)
            self._present_pos = angle
            self._t_pos = time.time()
            return angle
        return data

    def get_model_number(self) -> str | None:
        data = self._send_request(TYPE_MODEL)
        if data is not None:
            return data.decode()
        return data

    def get_cpr(self) -> int | None:
        data = self._send_request(TYPE_CPR)
        if data is not None:
            return int(data)
        return data

    def _send_request(self, rtype: bytes, data: bytes = None) -> bytes | None:
        tx_data = self._id_byte
        if data:
            tx_data += data
        response: Message = self._serial_manager.request(rtype, tx_data)
        status, err, err_value = self._verify_response(rtype, response)

        if not status:
            print(f"ERROR [{err}]: {err_value}")
            return None

        value = response.data.partition(SEP_CHAR)[2]
        return value

    def get_last_update_time(self):
        return self._last_comm_time

    def get_param(self, param):
        response = self._serial_manager.getParam(param)

        self._update_last_comm_time()
        return response

    def ping_device(self) -> bool | None: # SerialCommResponse:
        """Pings an encoder"""
        data = self._send_request(TYPE_CONNECTED)
        if data is not None:
            return data == DATA_TRUE
        return data

    def _verify_response(self, tx_type, response: Message | None) -> Tuple[bool, int, str]:
        """Verifies the response from the encoder
        Returns:
            bool: whether the response is valid
            int: error code (0 if no error)
            str: error message if any
        """
        # TODO - replace with real error codes

        # check response exists
        if not response:
            return False, -999, "NO RESPONSE"

        # response type matches
        if response.type == TYPE_ERROR:
            print("RESPONSE: Error -", repr(response))
            return False, -999, "ERROR RESPONSE"
        elif response.type == TYPE_DEBUG:
            print("RESPONSE: Debug -", repr(response))
            return False, -999, "DEBUG RESPONSE"
        elif response.type == TYPE_INFO:
            print("RESPONSE: Info -", repr(response))
            return False, -999, "INFO RESPONSE"

        if not (response.type.upper() == tx_type.upper()):

            ##ERR_MESSAGES
            print("RESPONSE:", str(response))
            return False, -999, f"TYPE MISMATCH: expected [{tx_type.decode()}] got [{response.type.decode()}]"

        # encoder id matches
        enc_id, _, value = response.data.partition(SEP_CHAR)
        if int(enc_id) != self._id:
            return False, -999, f"ENCODER ID - expected {self._id} got {enc_id.decode()}"

        return True, 0, ""

    def check_connected(self) -> bool:
        status = "\tStatus: UNKNOWN"
        prev_state = self._is_connected

        curr_state = self.ping_device()  # ping encoder device

        if curr_state is not None:   # valid response
            if curr_state and not self._is_connected:  # previously not connected but now found a device
                status = f"\tEncoder found! ({self._name})"
                print_c(status, Color.green)
            elif prev_state and not curr_state:
                # encoder was connected but now not found
                status = f"\tEncoder disconnected ({self._name})"
                print_c(status, Color.red)
            self._is_connected = curr_state
        else:
            # comm failure and device state has been changed
            if self._is_connected != prev_state:
                # TODO
                print("ERROR ???")

            # any errors - not connected TEMP?
            self._is_connected = False

        return self._is_connected

        # TODO make more robust way to check for connections when unplugged
        #  and replugged

    def check_reboot_status(self) -> SerialCommResponse:
        data = self._send_request(TYPE_MODEL)
        if data is None:
            print("Invalid response")
            return COMM_NOT_AVAILABLE, None, "Invalid response"  ## TODO is this okay?

        print("WWWWW", TYPE_WATCHDOG, data)

        return COMM_SUCCESS, data == DATA_TRUE, ""

    def _update_last_comm_time(self):
        self._last_comm_time = time.time()
        self._n_msg += 1

    def update_status(self, dt):
        t_last_update = self.get_last_update_time()
        if time.time() >= t_last_update + dt:

            self.check_connected()
            if not self._is_connected:
                return

        if self._n_msg >= REBOOT_CHECK_MSG_COUNT:
            self.check_reboot_status()  # resets _n_msg


class EncoderManager:
    dt_comm = 1  # 1 second between connected checks

    def __init__(self, encoders: Dict = None, baudrate=DEFAULT_BAUDRATE, iface_device=ARDUINO_UNO):
        self._encoders: Dict[str, Encoder] = {}

        self._serial_manager = SerialInterface(baud=baudrate,
                                               device_type=iface_device,
                                               )
        time.sleep(3)  # wait for device to initialise TODO - use a proper check

        # read any unread messages
        self._serial_manager.read_messages(suppress=True)

        # check serial device connected
        self._connected = self.heartbeat()

        if self._connected:
            print("Connection established!\n")

            print("Waiting for watchdog reboot check...")
            watchdog_count = self.watchdog()  # TODO implement a reboot on Arduino
            print("WD Count:", watchdog_count, "\n")

        print("Adding encoders...")
        if encoders:
            self.add_encoders(encoders)
        print("Encoders added!\n")

    def watchdog(self) -> int:
        count = 0
        watchdog = True
        while watchdog:
            response = self._serial_manager.request(TYPE_WATCHDOG, data=EMPTY_SEQ, suppress_text=True)
            watchdog = response.data == DATA_TRUE
            count += 1
            if count > 10:
                print("WATCHDOG FAILED")
        return count

    def close(self):
        self._serial_manager.close()

    def heartbeat(self) -> bool:
        beat, status, err = self._serial_manager.send_heartbeat()
        if status != COMM_SUCCESS:
            print(status)
            print(err)
        return beat

    def add_encoder(self, name, params):
        assert name not in self._encoders.keys()
        print(f"Adding encoder: {name}")

        # encoder_id, encoder_cpr = params
        encoder_id, config = params

        encoder = Encoder(name=name,
                          enc_id=encoder_id,
                          config=config,
                          serial_manager=self._serial_manager,
                          )

        if self._connected:
            if not encoder.check_connected():
                print_c(f"\tNot found! ({name})", Color.red)
        self._encoders[name] = encoder

    def add_encoders(self, encoders):
        for name, params in encoders.items():
            self.add_encoder(name, params)

    def reboot_encoder(self, name):
        raise NotImplementedError
        self._encoders[name].reboot()

    def get_homed(self, name) -> bool:
        return self._encoders[name].is_zeroed()

    def reset_homed(self, name):
        self._encoders[name].reset_zeroed()

    def set_home(self, name):
        self._encoders[name].set_home()

    def update_position(self, name):
        return self._encoders[name].update_position()

    def get_position(self, name):
        return self._encoders[name].get_present_pos()

    def is_encoder_connected(self, name):
        enc = self._encoders.get(name, None)
        if enc is None:
            print(f"Invalid encoder: '{name}'")
            return False
        # self._encoders[name].check_connected()
        return self._encoders[name].is_connected()

    def update(self):
        # TODO is this required?
        self._serial_manager.flush_rx()  # clear any stray data

        if not self.heartbeat():
            print("NO HEARTBEAT!")

            # clear any unread messages
            print(self._serial_manager.read_messages())
            self._serial_manager.flush_rx()

            return

        # update each encoder
        for encoder in self.encoders:
            encoder.check_connected()
            encoder.update_status(self.dt_comm)
            encoder.update_position()

    def get_model_number(self, name):
        return self._encoders[name].get_model_number()

    def get_cpr(self, name):
        return self._encoders[name].get_cpr()

    @property
    def encoders(self):
        return self._encoders.values()
