# Trimothee Software

This folder contains all Python software code for the Trimothee Ultramicrotome Targeting project.

## Folders

- **python_client/**: Main Python client code, including modules for communication, configuration, GUI, and axis control. This is the primary user-facing application for controlling and monitoring the system.
- **drivers/**: Python drivers for communicating with hardware components (e.g., Arduino encoder driver, Dynamixel motor driver). The Arduino encoder driver provides an interface to the encoder hardware and is typically run as a background process or service.
- **wheels/**: Custom Python wheel (.whl) files required for the project. These can be installed using pip.
    - **cmm_tools**: This Python package provides utility functions and tools used throughout, such as communication helpers or other shared functionality. Install it using the wheel file in this folder if it is not available on PyPI.
