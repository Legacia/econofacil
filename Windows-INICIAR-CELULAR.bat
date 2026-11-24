@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
title EconoFacil (modo celular)
if not exist ".venv\Scripts\python.exe" (
  echo O EconoFacil ainda nao foi instalado.
  echo De dois cliques em Windows-INSTALAR.bat primeiro.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" tools\run.py --rede
echo.
pause
