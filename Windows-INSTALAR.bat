@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
title EconoFacil - Instalador
echo == EconoFacil - Instalador (Windows) ==
echo.
set "PY="
for %%V in (3.12 3.13 3.11 3.10) do (
  if not defined PY (
    py -%%V -c "import sys" >nul 2>&1 && set "PY=py -%%V"
  )
)
if not defined PY (
  python -c "import sys; sys.exit(0 if (3,10)<=sys.version_info[:2]<=(3,13) else 1)" >nul 2>&1 && set "PY=python"
)
if not defined PY goto nopython
%PY% tools\installer.py
echo.
pause
exit /b

:nopython
echo Python (versao 3.10 a 3.13) nao foi encontrado neste computador.
echo.
where winget >nul 2>&1
if errorlevel 1 goto manual
set /p R=Deseja instalar o Python 3.12 agora, automaticamente? (S/N): 
if /i not "%R%"=="S" goto manual
winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
echo.
echo Python instalado. FECHE esta janela e de dois cliques em Windows-INSTALAR.bat novamente.
pause
exit /b

:manual
echo 1) Baixe o Python 3.12 em: https://www.python.org/downloads/windows/
echo 2) Na instalacao, MARQUE a caixa "Add python.exe to PATH".
echo 3) Depois de instalar, de dois cliques em Windows-INSTALAR.bat novamente.
start https://www.python.org/downloads/windows/
pause
exit /b
