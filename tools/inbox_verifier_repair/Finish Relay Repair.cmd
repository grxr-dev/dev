@echo off
rem Owner foreground only, AFTER this task's result is terminal/published.
python -B "%~dp0finish_repair.py" finish
pause
