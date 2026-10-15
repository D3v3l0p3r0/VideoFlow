@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" py -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade -r requirements-build.txt
if errorlevel 1 goto error
.venv\Scripts\python.exe build_exe.py
if errorlevel 1 goto error
echo.
echo Готово: dist\VideoFlow.exe
pause
exit /b 0
:error
echo.
echo Ошибка сборки VideoFlow.
pause
exit /b 1
