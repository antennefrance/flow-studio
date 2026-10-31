@echo off
rem -----------------------------------------------------------------------------
rem FLOW Studio Windows Desktop Launcher
rem Double-click this file in Windows Explorer to launch FLOW Studio.
rem -----------------------------------------------------------------------------

cd /d "%~dp0"

echo ======================================================================
echo  [FLOW Studio] Fast Lossless Offloaded Weights
echo  Universal Streaming Engine for Windows (CUDA / DirectML / CPU)
echo ======================================================================

rem Launch default web browser after short delay
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:8080"

rem Launch FLOW Studio Python Engine
python pyrite_app.py
pause

