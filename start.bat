@echo off
chcp 65001 > nul
cd /d "%~dp0"

if not exist savii.db (
  echo Собираю витрину из Excel...
  python etl.py
)

echo.
echo   SAVII Ask: http://127.0.0.1:8077   логин admin / пароль admin
echo   Ctrl+C — остановить
echo.

python -m uvicorn app:app --port 8077
