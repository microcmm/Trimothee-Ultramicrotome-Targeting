import os
import platform
import time

import tkinter as tk
from tkinter import ttk, messagebox
from collections import deque
from typing import Dict

from common import *

TXT_TICK = u'\u2713'
TXT_X = u'\u2715'

# Linux shutdown commands
REBOOT_CMD = "sudo reboot"
SHUTDOWN_CMD = "sudo shutdown -h now"

def reboot():
    # Linux only
    confirmation = messagebox.askokcancel("Reboot", "Are you sure you want to reboot?")
    if confirmation:
        print("Clicked Reboot")
        os.system(REBOOT_CMD)
        return
    print("Cancelled reboot")


def shutdown():
    # Linux only
    confirmation = messagebox.askokcancel("Shutdown", "Are you sure you want to shutdown?")
    if confirmation:
        print("Clicked Shutdown")
        os.system(SHUTDOWN_CMD)  # shutdown the system
        return
    print("Cancelled shutdown")


class EncoderUI:
    def __init__(self, controller, root, window_name):
        self.controller = controller
        self.root = root

        self.axis_frame = ttk.Frame(root, padding=10)
        self.knife_ui = AxisUI(self.axis_frame, label=DEV_KNIFE.capitalize())
        self.tilt_ui = AxisUI(self.axis_frame, label=DEV_TILT.capitalize())
        self.rotation_ui = AxisUI(self.axis_frame, label=DEV_ROT.capitalize())

        # Create an error label to display error messages
        self.status_bar = ttk.Label(root, text="", foreground="red", relief='sunken')

        # Pack the labels, scales, command box, button, and error label into
        # the window
        self.axis_frame.pack(side='top',
                             fill='both',
                             expand=True,
                             anchor='center',
                             )
        self.knife_ui.pack(side='left', padx=5)
        self.tilt_ui.pack(side='left', padx=5)
        self.rotation_ui.pack(side='left', padx=5)

        self.status_bar.pack(side='bottom',
                             fill='x',
                             expand=False,
                             anchor='center',
                             pady=5,
                             padx=5,
                             )

        self.menubar = MainMenu(self)

        # Root window behaviour
        self.root.title(window_name)
        self.root.minsize(600, 300)
        self.root.attributes('-fullscreen', True)
        self.root.config(menu=self.menubar)

        self._mouse_visible = True
        self._time_since_mouse = -1
        #self.root.config(cursor="none")
        self._hide_mouse()
        self.root.bind("<Motion>", self._on_mouse_move)
        self.root.bind("<Escape>", lambda e: root.attributes('-fullscreen', False))

    def set_display_averaging_len(self, n: int):
        """
        Set the moving average window size for angle display stability
        :param n: number of angles to store and average
        :return:
        """
        assert n > 0, "Averaging length must be 1 or greater"

        print("Setting display averaging window to", n)

        self.knife_ui.set_average_len(n)
        self.tilt_ui.set_average_len(n)
        self.rotation_ui.set_average_len(n)

    def _on_mouse_move(self, event):
        self._show_mouse()
        self._time_since_mouse = time.time()

    def _show_mouse(self):
        if not self._mouse_visible:
            self.root.config(cursor="arrow")
            self._mouse_visible = True

    def _hide_mouse(self, dt = 1):
        if self._mouse_visible and (time.time() - self._time_since_mouse >= dt):
            self.root.config(cursor="none")
            self._mouse_visible = False
        self.root.after(dt * 1000, self._hide_mouse)

    def set_status(self, status: str, color: str = "red"):
        self.status_bar.config(text=status, foreground=color)

    def quit(self):
        print("Quitting")
        self.controller.quit()
        self.root.quit()


class AxisUI(ttk.Frame):
    PADDING = (10, 5)  # X, Y
    N_CHARS = 7
    ANGLE_UNKNOWN = "???"
    N_AVE_DEFAULT = 1

    def __init__(self, parent, label, params=None, *args, **kwargs):
        super().__init__(master=parent,
                         padding=self.PADDING,
                         relief='groove',  # flat, groove, raised, ridge, solid, or sunken
                         *args, **kwargs)
        # self.angle = 0.0
        self.name = label

        self._params: dict = {}
        if params is not None:
            self.set_params(params)

        # list of angles for moving average
        self._n_ave = self.N_AVE_DEFAULT         # number of angles to average
        self._angles = deque(maxlen=self._n_ave) # list of angles
        self._angle_ave = 0.0                    # average angle

        # style entries for this axis label and zero buttons
        self._zero_btn_style: str = f'zero_{label}.TButton'
        self._name_style: str = f'name_{label}.TLabel'
        self._angle_style: str = f'angle_{label}.TLabel'

        self._font = ('Helvetica', 24, 'bold')
        self._angle_font = ('Courier New', 24, 'bold')

        self._axis_style = ttk.Style()
        self._axis_style.configure(self._name_style, font=self._font)
        self._axis_style.configure(self._angle_style, font=self._angle_font)

        self.label_name = ttk.Label(self, text=f"{label}", anchor='center', style=self._name_style)
        self.label_angle = ttk.Label(self, text=self.ANGLE_UNKNOWN, anchor='center', style=self._angle_style)#'e')
        self.btn_zero = ttk.Button(self, style=self._zero_btn_style)  # bind_zero method must be connected to a callback

        self.display_zeroed(False)
        self.display_attached(False)

        self.bind('<Configure>', self.on_resize)

    def set_params(self, params):
        self._params = params

    def bind_zero(self, callback):
        """Bind zero button click to external callback."""
        self.btn_zero.config(command=callback)

    def display_attached(self, state: bool):
        """
        Update UI to reflect whether the axis is attached
        """
        if state:
            self.label_name.config(foreground="green")
            self.btn_zero.config(state='normal')
        else:
            self.label_name.config(foreground="red")
            self.btn_zero.config(state='disabled')
            self.display_angle(self.ANGLE_UNKNOWN)

    def display_zeroed(self, state):
        # set button text
        zeroed_txt = "Zero " + (TXT_TICK if state else TXT_X)
        self.btn_zero.config(text=zeroed_txt)

        # set button colour
        self._axis_style.configure(self._zero_btn_style, foreground=('green' if state else 'red'))

    def set_average_len(self, n):
        self._n_ave = n
        self._angles = deque(self._angles, maxlen=n)

        if len(self._angles) > 0:  # calculate the correct average - O(N)
            self._angle_ave = sum(self._angles) / len(self._angles)
        else:
            self._angle_ave = 0.0

    def set_angle(self, angle: float):
        """
        Add a new angle to the list of angles and update the average angle.
        O(1) time complexity for averaging update calculations.
        :param angle:
        :return:
        """

        # TODO make this an instance attribute and update on modification??
        backlash = self._params.get("backlash", 0.0)
        invert = self._params.get("invert", 0)

        # invert display angle
        if invert:  # TODO: test this properly
            angle = -angle

        prev_angle = self._angles[-1] if len(self._angles) > 0 else 0.0

        if len(self._angles) == self._n_ave:     # queue is full
            # remove oldest angle from average and add new angle
            angle_pop = self._angles.popleft()            # remove oldest angle
            self._angle_ave += (angle - angle_pop) / self._n_ave
        else:                                   # queue is not full
            queue_len = len(self._angles)

            # update average angle
            self._angle_ave = (self._angle_ave * queue_len + angle) / (queue_len+1)

        # add new angle to list
        self._angles.append(angle)

        # modify displayed angle before displaying
        disp_angle = self._angle_ave

        # backlash compensation
        # determine step direction and size for multi-valued queue
        step_dir = 1 if angle > prev_angle else 0
        step_size = abs(angle - prev_angle)
        if step_dir == 0:   # stepped in reverse direction
            if step_size >= backlash: # axis engaged if step size is greater than backlash
                disp_angle = self._angle_ave - backlash
        self.display_angle(disp_angle)

    def display_angle(self, angle):
        if isinstance(angle, str):
            self.label_angle.config(text=angle)
        else:
            if abs(angle) < 0.01:  # ignore negative zeros (very small numbers)
                angle = abs(angle)
            self.label_angle.config(text=f"{angle: {self.N_CHARS}.2f}°")

    def on_resize(self, event):
        ratio = 20  # fractional size of text relative to frame(?) size

        new_size = min(event.width // ratio, event.height // ratio)
        angle_font = (self._angle_font[0], 2*new_size, 'bold')
        font = (self._font[0], new_size, 'bold')

        self.label_angle.config(font=angle_font)

        self._axis_style.configure(self._name_style, font=font)
        self._axis_style.configure(self._zero_btn_style, font=font)

    def pack(self, *args, **kwargs):
        self.label_name.pack(side='top', fill='both', expand=True, anchor='center')
        self.label_angle.pack(side='top', fill='both', expand=True, anchor='center', pady=10)
        self.btn_zero.pack(side='top', fill='both', expand=True, anchor='center')

        super().pack(ipadx=self.PADDING[0],
                     ipady=self.PADDING[1],
                     fill='both',
                     expand=True,
                     anchor='center',
                     *args, **kwargs)


class ParameterWindow(tk.Toplevel):
    def __init__(self, parent, params: Dict = None):
        super().__init__(parent)
        self.title("Set Scale")
        self.resizable(False, False)
        self.parent = parent

        self._frame_params = tk.Frame(self, relief="groove")
        self._frame_btns = ttk.Frame(self)

        self.btn_save = ttk.Button(self._frame_btns, text="Save", width=20, command=self.on_save)
        self.btn_cancel = ttk.Button(self._frame_btns, text="Cancel", width=20, command=self.on_cancel)

        self._ui_boxes = []  # persistent list of UI elements
        self._param_vars = {}

        self.make_grid(params)

        self._frame_params.pack(fill='both', expand=True, padx=10, pady=10)
        self._frame_btns.pack(side="bottom", fill='x', expand=True, padx=5, pady=5)

        self.btn_cancel.pack(side="right",fill='none',expand=False,padx=5, pady=5)
        self.btn_save.pack(side="right", fill='none', expand=False,padx=5, pady=5)


        self.bind('<Escape>', lambda e: self.on_cancel())
        self.focus_set()

    def make_grid(self, config):
        grid_config = {'padx': 5, 'pady': 5, 'sticky': 'ew'}

        # insert column headers to grid
        columns = ['', 'Scale', 'Backlash', 'Min', 'Max', 'Invert']
        for i_col, col in enumerate(columns):
            header = ttk.Label(self._frame_params, text=col)
            header.grid(row=0, column=i_col, **grid_config)

        # insert axis parameters into grid
        row = 1
        for axis, params in config.items():
            # create parameter variables then store for persistent use
            scale_var =    tk.DoubleVar(value=params.get('scale',    1.0))
            backlash_var = tk.DoubleVar(value=params.get('backlash', 0.0))
            min_var =      tk.DoubleVar(value=params.get('min',   -180.0))
            max_var =      tk.DoubleVar(value=params.get('max',    180.0))
            invert_var =   tk.IntVar(   value=params.get('invert',     0))
            self._param_vars[axis] = {"scale": scale_var, "backlash": backlash_var, "min": min_var, "max": max_var, "invert": invert_var}

            # create UI elements
            label =        ttk.Label(self._frame_params, width=10, text=axis.capitalize())
            scale_box =    ttk.Entry(self._frame_params, width=12, justify='right', textvariable=scale_var)
            backlash_box = ttk.Entry(self._frame_params, width=12, justify='right', textvariable=backlash_var)
            min_box =      ttk.Entry(self._frame_params, width=8, justify='right', textvariable=min_var)
            max_box =      ttk.Entry(self._frame_params, width=8, justify='right', textvariable=max_var)
            invert_box = ttk.Checkbutton(self._frame_params, variable=invert_var)

            # store persistent UI elements
            self._ui_boxes.append((label, scale_box, backlash_box, min_box, max_box, invert_box))

            # place UI elements in grid
            label.grid(       row=row, column = 0, **grid_config)
            scale_box.grid(   row=row, column = 1, **grid_config)
            backlash_box.grid(row=row, column = 2, **grid_config)
            min_box.grid(     row=row, column = 3, **grid_config)
            max_box.grid(     row=row, column = 4, **grid_config)
            invert_box.grid(  row=row, column = 5, **grid_config)

            row += 1

    def on_cancel(self):
        print("Cancel")
        self.destroy()

    def on_save(self):
        print("Save")

        # retrieve values from UI elements and store in structured dictionary
        new_params = {axis:
                          {param: self._param_vars[axis][param].get()
                           for param in self._param_vars[axis]}
                      for axis in self._param_vars}
        print(new_params)

        # update parameters in controller and save to file
        self.parent.controller.set_params(new_params)
        self.parent.controller.save_config() # TODO - only save if changes were made?

        # close the window
        self.destroy()


class MainMenu(tk.Menu):
    def __init__(self, parent):
        super().__init__(parent.root, tearoff=0, font=("", 12))

        self.controller = parent.controller
        self.parent = parent

        self._file_menu = tk.Menu(self, tearoff=0)
        self._file_menu.add_command(label="Exit", command=self.quit)
        # NB. shutdown option available for Linux (Raspberry Pi)
        if platform.system() == "Linux":
            self._file_menu.add_separator()
            self._file_menu.add_command(label="Reboot", command=reboot)
            self._file_menu.add_command(label="Shutdown", command=shutdown)

        self._edit_menu = tk.Menu(self, tearoff=0)
        self._edit_menu.add_command(label="Set parameters", command=self.set_params)

        self._clear_zero_menu = tk.Menu(self, tearoff=0)
        self._clear_zero_menu.add_command(label="Reset Knife", command=lambda: self.controller.clear_zero_flag(DEV_KNIFE))
        self._clear_zero_menu.add_command(label="Reset Tilt", command=lambda: self.controller.clear_zero_flag(DEV_TILT))
        self._clear_zero_menu.add_command(label="Reset Rotation", command=lambda: self.controller.clear_zero_flag(DEV_ROT))
        self._clear_zero_menu.add_separator()
        self._clear_zero_menu.add_command(label="Reset All", command=lambda: self.controller.clear_zero_flag())
        self._edit_menu.add_cascade(label="Clear zero flag", menu=self._clear_zero_menu)

        self.add_cascade(label="File", menu=self._file_menu)
        self.add_cascade(label="Edit", menu=self._edit_menu)

    def on_resize(self, event):
        # Calculate the new font size based on the window size
        new_size = min(event.width // 20, event.height // 20)
        self.config(font=("Helvetica", new_size))

    def set_params(self):
        param_table = self.controller.get_params()
        print(param_table)
        param_win = ParameterWindow(self, params=param_table)
        print("Config parameters")

    def quit(self):
        print("Clicked Quit")
        self.parent.quit()
