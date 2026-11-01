@echo off
setlocal
cd /d "%USERPROFILE%\Documents\Codex\Muse"
python -B "%USERPROFILE%\Documents\Codex\Muse\dev\tools\inbox_future\finish_future.py" finish
set "FutureResult=%errorlevel%"
pause
exit /b %FutureResult%
