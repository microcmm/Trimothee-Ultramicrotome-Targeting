from typing import Tuple, Any

from serial_scanner.scanner import SerialDeviceInfo

# used commonly downstream
from cmm_tools.cmm_comms.cmm_serial import DATA_TRUE, EMPTY_SEQ, SEP_CHAR, Message
from cmm_tools.cmm_comms.cmm_serial.devices.arduino import (ARDUINO_UNO, ARDUINO_MEGA2560, DFROBOT_BEETLE,
                                                            K_CPR, BITSIZE_32, DRIVE_DIR_NORMAL, DRIVE_DIR_REVERSE,
                                                            TYPE_SET_ZERO, TYPE_ANGLE, TYPE_MODEL, TYPE_CPR, TYPE_CONNECTED)


SerialCommResponse = Tuple[Any, int, str]
DEFAULT_BAUDRATE = 57600

DEGREES_PER_REV = 360

DEV_KNIFE = "knife"
DEV_TILT = "tilt"
DEV_ROT = "rotation"

STATUS_OK = "OK"
STATUS_BAD = "BAD"
STATUS_MISSING = "DEVICE MISSING"
STATUS_VAL = "v"

LEN_CMD_VALUED = 2  # length of a valued command key (e.g., LA, LS)
CMD_SET_HOME = "HO"
CMD_RESET_HOMED = "RH"
REQ_GET_HOMED = "GH"
REQ_GET_SERIAL = "GSER"
REQ_GET_POS = "POS"
REQ_GET_ATT = "ATT"


TOPIC_OTHER_REQ = "OtherRequest"

TOPIC_CMD_ENC = "TargetEncoderCMDs"
TOPIC_CMD = "CMDs"
TOPIC_CMD_DROPBOX = "CMDDropBox"
TOPIC_REPLY_DEV_STATUS = "VAL_DEV"
TOPIC_REPLY_DROPBOX = "VAL_DROP"
TOPIC_REPLY_ATTACHED = "VAL_ATT"
TOPIC_REPLY_POS = "VAL_POS"
TOPIC_REPLY_HOMED = "VAL_HOMED"


COMM_SUCCESS = 0  # tx or rx packet communication success
COMM_PORT_BUSY = -1000  # Port is busy (in use)
COMM_TX_FAIL = -1001  # Failed transmit instruction packet
COMM_RX_FAIL = -1002  # Failed get status packet
COMM_TX_ERROR = -2000  # Incorrect instruction packet
COMM_RX_WAITING = -3000  # Now recieving status packet
COMM_RX_TIMEOUT = -3001  # There is no status packet
COMM_RX_CORRUPT = -3002  # Incorrect status packet
COMM_NOT_AVAILABLE = -9000  #
