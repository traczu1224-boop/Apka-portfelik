@echo off
setlocal
if not exist .venv (
  python -m venv .venv
)
call .venv\Scripts\activate
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name ApkaPortfelik main.py

set "ISCC="
for %%I in ("%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" "%ProgramFiles%\Inno Setup 6\ISCC.exe") do (
  if exist "%%~I" set "ISCC=%%~I"
)
if not defined ISCC (
  for /f "delims=" %%I in ('where ISCC.exe 2^>nul') do (
    set "ISCC=%%~I"
    goto :found_iscc
  )
)
:found_iscc
if defined ISCC (
  "%ISCC%" "installer\ApkaPortfelik.iss"
  echo Zbudowano instalator: dist\ApkaPortfelik-Setup.exe
) else (
  echo Nie znaleziono Inno Setup. Zainstaluj Inno Setup 6, aby zbudowac instalator.
)
endlocal
