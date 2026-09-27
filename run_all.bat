@echo off
REM Runs the full analysis. Any options are passed on, e.g. run_all.bat -RawDir "D:\BRFSS"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_all.ps1" %*
pause
