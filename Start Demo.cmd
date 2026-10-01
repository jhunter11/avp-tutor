@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  python "%~dp0demo.py" up --open %*
) else (
  py -3 "%~dp0demo.py" up --open %*
)
exit /b %errorlevel%
