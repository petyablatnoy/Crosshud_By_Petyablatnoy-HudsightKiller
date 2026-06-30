@echo off
NET SESSION >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    powershell -command "Start-Process -Verb RunAs -FilePath '%0'"
    EXIT /B
)
cd /d "%~dp0"
python build.py
pause