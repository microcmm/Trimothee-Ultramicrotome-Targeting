@echo off

set CONFIG_PATH=src\config.json
set DRIVER_BAT=src\drivers\run_driver.bat
set CLIENT_BAT=src\python_client\run_client.bat

REM Resolve CONFIG_PATH to absolute path
for %%I in ("%CONFIG_PATH%") do set ABS_CONFIG_PATH=%%~fI
for %%I in ("%DRIVER_BAT%") do set ABS_DRIVER_BAT=%%~fI
for %%I in ("%CLIENT_BAT%") do set ABS_CLIENT_BAT=%%~fI

echo Using config file: %ABS_CONFIG_PATH%

REM Check if TRIMOTHEE_VENV is defined
IF NOT DEFINED TRIMOTHEE_VENV (
    echo ERROR: TRIMOTHEE_VENV environment variable is not defined.
    echo Please set TRIMOTHEE_VENV to your python VENV directory before running this script. E.g., set TRIMOTHEE_VENV=C:\path\to\your\venv
    exit /b 1
)

echo Virtual environment activated: %TRIMOTHEE_VENV%
CALL "%TRIMOTHEE_VENV%\Scripts\activate.bat"

echo Running driver server...
rem CALL .\src\drivers\run_driver.bat "%ABS_CONFIG_PATH%"
start "Arduino Driver" cmd /c ""%ABS_DRIVER_BAT%" "%ABS_CONFIG_PATH%""

echo Running display client...
CALL .\src\python_client\run_client.bat "%ABS_CONFIG_PATH%"
