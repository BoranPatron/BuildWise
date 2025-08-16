@echo off
REM BuildWise Database Reset - Windows Batch Script
REM Führt das Python-Skript automatisch aus

echo.
echo ====================================
echo  BuildWise Database Auto-Reset
echo ====================================
echo.

REM Ins richtige Verzeichnis wechseln
cd /d "%~dp0"

REM Python-Skript ausführen
python reset_database_auto.py %*

REM Kurz warten damit man das Ergebnis sehen kann
if not "%1"=="--quiet" (
    echo.
    echo Druecke eine beliebige Taste zum Beenden...
    pause >nul
)
