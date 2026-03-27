from __future__ import annotations

import atexit
import threading
from gui import *
import argparse

from common import *
from comms import CommsHandler, DEFAULT_SERVER_IP, DEFAULT_SERVER_PORT
from config_handler import Config
from axis import Axis


DEFAULT_PARAMS = {DEV_KNIFE:
                      {"scale": 94.0138, "backlash": 0.0, "min": -30.0, "max": 30.0, "invert": 0},
                  DEV_TILT:
                      {"scale": 14.0127, "backlash": 0.0, "min": -22.0, "max": 22.0, "invert": 0},
                  DEV_ROT:
                      {"scale": 7.997, "backlash": 0.0, "min": -180.0, "max": 180.0, "invert": 0},
                  }


class EncoderReadoutApp:
    def __init__(self, root, window_name: str, config: Dict | Config = None):  # , dt=1000):
        self._config = config
        if config is None:
            self._config = Config()

        if "axis_config" not in self._config:
            print("NO AXIS CONFIG")
            self._params = DEFAULT_PARAMS
            self._config["axis_config"] = self._params
        else:
            self._params = self._config["axis_config"]

        server_cfg = self._config.get("server_address", {})
        host = server_cfg.get("host", DEFAULT_SERVER_IP)
        port = server_cfg.get("port", DEFAULT_SERVER_PORT)
        server_address = (host, port)

        self.comms_handler = CommsHandler(server_address=server_address)  # handler for device communication
        self._running = False

        self.display = EncoderUI(self, root, window_name)
        averaging_len = self._config.get("averaging_window", 1)
        self.display.set_display_averaging_len(averaging_len)  # SMA window length (1 = no averaging)

        # create axes
        self.knife_axis =    Axis(name=DEV_KNIFE, params=self._params[DEV_KNIFE], comms_handler=self.comms_handler)
        self.tilt_axis =     Axis(name=DEV_TILT,  params=self._params[DEV_TILT],  comms_handler=self.comms_handler)
        self.rotation_axis = Axis(name=DEV_ROT,   params=self._params[DEV_ROT],   comms_handler=self.comms_handler)
        self._axes = [self.knife_axis, self.tilt_axis, self.rotation_axis]

        # connect axis to their displays
        self.knife_axis.set_display(self.display.knife_ui)
        self.tilt_axis.set_display(self.display.tilt_ui)
        self.rotation_axis.set_display(self.display.rotation_ui)

    def save_config(self, filepath: str = None):
        self._config.save(filepath)

    def clear_zero_flag(self, device: str = DEV_ALL):
        for axis in self._axes:
            if device == DEV_ALL or axis.name == device:
                axis.request_clear_zeroed()
                self._update_zeroed_state(axis)

    def get_params(self):
        return self._params

    def set_params(self, params: dict):
        self._params.update(params)  # update existing with new values
        print("XXRT")
        print(self._params)
        print(self._config)

        for axis in self._axes:
            axis.set_params(self._params[axis.name])

    def display_status(self, status: str, color: str = "red"):
        self.display.set_status(status, color)

    def update_angle_labels(self):
        for axis in self._axes:
            axis.request_angle()

    def update(self):
        # update connected state
        comms_status = self.comms_handler.update()
        if comms_status:
            self.display_status(comms_status, color="black")

        if self.comms_handler.connected():
            self.update_att_state()
            self.update_zeroed_state()

            # update device angles
            for axis in self._axes:
                if axis.is_attached():
                    status = axis.request_angle()
                    if not status:
                        axis.request_attached()
                else:
                    axis.request_attached()

    def update_att_state(self):
        for axis in self._axes:
            axis.request_attached()

    def _update_zeroed_state(self, axis):
        zeroed_prev = axis.is_zeroed
        zeroed_curr = axis.request_zeroed()

        if zeroed_curr != zeroed_prev:  # zero state changed
            axis.get_display().display_zeroed(zeroed_curr)

    def update_zeroed_state(self):
        for axis in self._axes:
            self._update_zeroed_state(axis)

    def run(self, dt=0.01):
        self._running = True
        while self._running:
            self.update()
            time.sleep(dt)
        print("EXITING")
        self.on_exit()

    def stop(self):
        self._running = False

    def on_exit(self):
        print("Exiting...")
        self.comms_handler.close()
        self.stop()

    def quit(self):
        self.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Arduino Encoder Driver")
    parser.add_argument("--config", required=True, help="Path to the configuration JSON file")
    args = parser.parse_args()
    CONFIG_FILE = args.config

    root = tk.Tk()
    root.minsize(600, 300)

    app = EncoderReadoutApp(root,
                            window_name="Angle Display",
                            config=Config(CONFIG_FILE),
                            #dt=50,
                            )
    root.attributes('-fullscreen', True)

    root.bind("<Escape>", lambda e: root.attributes('-fullscreen', False))
    atexit.register(app.on_exit)

    # start thread for timed app requests
    data_thread = threading.Thread(name="EncoderReaderThread",
                                   target=app.run,
                                   daemon=True)
    data_thread.start()
    root.mainloop()
