@echo off
setlocal
cd /d "%USERPROFILE%\Documents\Codex\Muse"
python -B "%USERPROFILE%\Documents\Codex\Muse\dev\tools\inbox_exact_one\finish_once.py" finish
set "FinishResult=%errorlevel%"
pause
exit /b %FinishResult%
