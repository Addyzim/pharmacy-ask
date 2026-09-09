@echo off
chcp 65001 > nul
cd /d "%~dp0"

where pythonw > nul 2>&1
if %errorlevel%==0 (
  start "" pythonw "launcher.pyw"
  exit /b
)

echo Не найден pythonw — запускаю в консоли.
python launcher.pyw
