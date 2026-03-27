# Trimothee Ultramicrotome Targeting

This project contains resources for the Trimothee Ultramicrotome Targeting system developed at the Centre for Microscopy and Microanalysis (UQ). The repository includes software, firmware, CAD and drawings, and electronics designs.

## Project Structure

- **src/**: Python software code (client, drivers, requirements, etc.)
- **firmware/**: Embedded/firmware code for microcontrollers
- **CAD_files/**: CAD files for mechanical design
- **electronics/**: Electronics schematics, PCB layouts, and related files
- **run_trimothee.bat / run_trimothee.sh**: Entry-point scripts for running the software

## Prerequisites
- Python 3.11 or newer is recommended
- pip (Python package installer). Some packages may not be available via Conda.
- cmm_tools (for running the Python client, see src/README.md for details). A precompiled wheel is available in src/wheels/ for easy installation.

## Installation

In a terminal (or command prompt on Windows) activate the Python environment you intend to use for the project (if applicable) and navigate to the project root.

1. **Install cmm_tools package from wheel**
   ```sh
   pip install src/wheels/cmm_tools.whl
   ```
   The cmm_tools package may have a different name depending on the version and platform. Adjust the command to suit the actual filename in the wheels directory.
2. **Install Python dependencies**
   ```sh
   pip install -r src/requirements.txt
   ```

## Configuration

The software configuration file `config.json` is located in the `src/` directory. Adjust this file as needed for your setup or use the default.

## Running the Software

Call the provided `run_trimothee.bat` (Windows) or `run_trimothee.sh` (Linux/Raspberry Pi) script to launch the driver and UI client.

<p align="center">
  <img src="./docs/img_trimothee.pdf" width="350" title="Trimothee">
</p>
![Trimothee](./docs/img_trimothee)
