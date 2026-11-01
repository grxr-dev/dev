@echo off
rem Run once from the owner's desktop AFTER issue106 has returned its terminal result.
python -B "%~dp0finish_receipt.py" finish
pause
