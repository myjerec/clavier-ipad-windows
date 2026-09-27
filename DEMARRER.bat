@echo off
cd /d "%~dp0"
set "CLAVIER_PY=python"
python -c "import sys; assert sys.version_info >= (3,11)" >nul 2>&1
if errorlevel 1 set "CLAVIER_PY=py -3"
%CLAVIER_PY% -c "import cryptography, qrcode, pystray, PIL" >nul 2>&1
if errorlevel 1 (
  echo Installation de la dependances...
  %CLAVIER_PY% -m pip install -r requirements.txt
  if errorlevel 1 goto erreur
)
%CLAVIER_PY% companion.py --start
if errorlevel 1 goto erreur
exit /b
:erreur
echo Impossible de demarrer. Python 3.11 ou plus recent est requis.
pause
