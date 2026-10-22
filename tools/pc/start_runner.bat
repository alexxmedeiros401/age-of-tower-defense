@echo off
title AgeOfTD build runner
cd /d "%~dp0"
if not exist logs mkdir logs
if not exist "py\python\python.exe" (
  echo Downloading Python 3.13 - one time, about 50 MB...
  powershell -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -UseBasicParsing -Uri 'https://github.com/astral-sh/python-build-standalone/releases/download/20261021/cpython-3.13.17%%2B20261021-x86_64-pc-windows-msvc-install_only.tar.gz' -OutFile 'py.tgz'"
  if not exist py mkdir py
  tar -xzf py.tgz -C py
  del py.tgz
)
if not exist "py\python\python.exe" (
  echo Could not set up Python. Tell Claude.
  pause
  exit /b 1
)
"py\python\python.exe" -c "import bpy, numpy, scipy, skimage, PIL" >nul 2>nul
if errorlevel 1 (
  echo Installing Blender's Python module and libraries - one time, about 450 MB, a few minutes...
  "py\python\python.exe" -m pip install --disable-pip-version-check --no-warn-script-location bpy==5.2.2 numpy scipy scikit-image pillow > logs\pip_install.log 2>&1
  "py\python\python.exe" -c "import bpy, numpy, scipy, skimage, PIL; print('Blender', bpy.app.version_string, 'ready')"
)
if exist "repo\tools\pc\runner.py" copy /y "repo\tools\pc\runner.py" "runner.py" >nul
"py\python\python.exe" runner.py
echo.
echo The runner stopped. You can close this window.
pause
