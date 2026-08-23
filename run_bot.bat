@echo off
title Telegram Malware Guard Bot
echo ===================================================
echo   🛡️ Telegram Malware & Threat Guard Bot Launcher
echo ===================================================
echo.

if not exist .env (
    echo [!] Warning: .env file not found!
    echo [*] Creating .env from .env.example...
    copy .env.example .env
    echo [*] Please edit .env with your TELEGRAM_BOT_TOKEN and VIRUSTOTAL_API_KEY.
    echo.
    pause
    exit /b
)

echo [*] Checking Python dependencies...
python -m pip install -r requirements.txt
echo.
echo [*] Starting Telegram Security Bot...
python telegram_security_bot.py
pause
