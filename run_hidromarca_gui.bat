@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo.
echo === HidroMarca GUI ===
echo.

python --version >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python no esta disponible en PATH.
  echo Instala Python 3.10+ y vuelve a intentar.
  pause
  exit /b 1
)

python -c "import cv2, numpy, PIL" >nul 2>nul
if errorlevel 1 (
  echo Instalando dependencias...
  python -m pip install -r requirements.txt
  if errorlevel 1 (
    echo ERROR: No se pudieron instalar las dependencias.
    pause
    exit /b 1
  )
)

python "%~dp0src\hidromarca_gui.py"

if errorlevel 1 (
  echo.
  echo ERROR: HidroMarca GUI fallo.
  pause
  exit /b 1
)
