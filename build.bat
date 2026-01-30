@echo off
setlocal
if not exist .venv (
  python -m venv .venv
)
call .venv\Scripts\activate
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name ApkaPortfelik main.py
endlocal
