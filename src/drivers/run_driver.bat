call "%TRIMOTHEE_VENV%/Scripts/activate.bat"
cd /d "%~dp0"

REM Require the first argument as the config path
if %1=="" (
    echo ERROR: No config path provided. Please call this script with the config file path as the first argument.
    exit /b 1
)
set CONFIG_PATH=%1

REM echo Running Arduino Encoder Driver with config: %CONFIG_PATH%
python "./arduino_encoder_driver/main.py" --config %CONFIG_PATH%
