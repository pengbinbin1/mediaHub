@echo off
rem MiniHub build script (ASCII only, run from project root)
cd /d "%~dp0"
".venv\Scripts\pyinstaller.exe" --noconfirm --clean --windowed --name MiniHub --icon "app\resources\icon.ico" --add-data "app\resources\icon.ico;resources" --hidden-import pymupdf run.py
echo.
echo Build done: dist\MiniHub\MiniHub.exe
