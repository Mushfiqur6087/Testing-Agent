@echo off
echo Starting Agent Interface...

REM Check if venv exists, if not create it
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Start Flask server
echo Starting Flask server...
python main.py

REM Deactivate virtual environment on exit
deactivate 