@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -m venv .venv
  .venv\Scripts\python.exe -m pip install --upgrade pip
)
.venv\Scripts\python.exe -c "import yt_dlp, certifi, truststore, customtkinter, PIL" >nul 2>&1
if errorlevel 1 .venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe videoflow.py
if errorlevel 1 pause

