from typing import Any

DIR_FWD = 1
DIR_REV = 0

class Axis:
    def __init__(self, name, comms_handler, display=None, params:dict=None):
        self._name: str = name
        self._comms_handler = comms_handler

        self._params: dict = None
        self._scale: float = None
        # self._backlash: float = None
        # self._max: float = None
        # self._min: float = None
        # self._invert: bool = None

        self._display = None
        if display is not None:
            self.set_display(display)

        self.set_params(params)

        self._angle: float = 0.0
        self._curr_dir = DIR_FWD
        self._last_step = 0.0

        self._attached = None
        self._model = None
        self._zeroed = None

    def set_params(self, params: dict):
        self._params = params
        if self._display is not None:
            self._display.set_params(params)
        self.refresh_params()

    def refresh_params(self):
        print(f"Refreshing axis params: {self._name}")
        self._scale = self._params.get("scale", 1.0)
        # self._backlash = self._params.get("backlash", 0.0)
        # self._max = self._params.get("max", 360.0)
        # self._min = self._params.get("min", 0.0)
        # self._invert = self._params.get("invert", 0) != 0

    @property
    def name(self):
        return self._name

    def set_display(self, display: Any):
        """Assign a display object to the axis - handles displaying axis info
        info such as through a GUI.
        """
        self._display = display
        # bind display's zero method (button) to the request_zero method
        self._display.bind_zero(self.request_zero)
        self._display.set_params(self._params)

    # def set_scale(self, scale: float):
    #     self._scale = scale
    #
    # def set_backlash(self, backlash: float):
    #     self._backlash = backlash
    #
    # def set_max(self, max_angle: float):
    #     self._max = max_angle
    #
    # def set_min(self, min_angle: float):
    #     self._min = min_angle
    #
    # def set_invert(self, invert: bool):
    #     self._invert = invert

    def get_display(self):
        return self._display

    def request_attached(self) -> bool:
        state = self._comms_handler.get_attached(self._name)

        if state != self._attached:  # update UI if state has changed
            self._display.display_attached(state)
        self._attached = state
        return state

    def is_attached(self):
        return self._attached

    def request_model(self) -> bool:
        model = self._comms_handler.get_model(self._name)

        if model != self._model:
            self._model = model
            return True

        if model is None:
            return False
        return True

    @property
    def is_zeroed(self):
        return self._zeroed

    def request_zeroed(self) -> bool:
        zeroed = self._comms_handler.get_zeroed(self._name)
        if zeroed != self._zeroed:
            self._zeroed = zeroed

        return zeroed

    def request_clear_zeroed(self) -> bool:
        zeroed = self._comms_handler.reset_zeroed(self._name)
        if zeroed != self._zeroed:
            self._zeroed = zeroed

        return zeroed

    def request_zero(self) -> bool:
        """
        Send a request to zero the axis
        :return: True if the request was successful, False otherwise
        """
        status = self._comms_handler.set_zero(self._name)
        if status:
            self.request_angle()  # update angle after zeroing
        return status

    def request_angle(self) -> bool:
        """
        Send a request for the current angle of the axis
        :return: True if the request was successful, False otherwise
        """

        angle = self._comms_handler.get_angle(self._name)
        if angle is not None:
            self.set_angle(angle)
            return True
        return False

    def set_angle(self, angle: float):
        """
        Update the angle of the axis and display the scaled version
        :param angle: actual angle on encoder
        :return: None # the scaled angle
        """
        self._angle = angle
        angle_scaled = angle / self._scale

        #display_angle = angle_scaled + self._backlash
        self._display.set_angle(angle_scaled)  # display the angle
        # self.label_angle.config(text=f"{self.angle}°")

    def get_angle(self):
        return self._angle
