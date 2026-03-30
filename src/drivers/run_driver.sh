#!/bin/bash

# Exit on error
set -e

# Check if TRIMOTHEE_VENV is defined
if [ -z "$TRIMOTHEE_VENV" ]; then
  echo "ERROR: TRIMOTHEE_VENV environment variable is not defined."
  echo "Please set TRIMOTHEE_VENV to your python venv directory before running this script."
  exit 1
fi

# Check if config path is provided as the first argument
if [ -z "$1" ]; then
  echo "ERROR: No config path provided. Please call this script with the config file path as the first argument."
  exit 1
fi
CONFIG_PATH="$1"

# Activate the virtual environment
source "$TRIMOTHEE_VENV/activate"

python ./arduino_encoder_driver/main.py --config "$CONFIG_PATH"
