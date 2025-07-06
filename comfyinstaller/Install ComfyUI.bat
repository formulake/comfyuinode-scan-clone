@echo off
setlocal enabledelayedexpansion

:: --- Check for Git ---
echo Checking for Git installation...
git --version >nul 2>&1
if errorlevel 1 (
    echo Git is not installed or not in PATH.
    goto end
)

:: --- Check for Python 3.12 ---
echo Checking for Python 3.12...
for /f "tokens=2 delims= " %%A in ('python --version') do set PY_VER=%%A
for /f "tokens=1,2 delims=." %%B in ("%PY_VER%") do (
    set MAJOR=%%B
    set MINOR=%%C
)

if not "!MAJOR!"=="3" (
    echo Python 3.x is required. Found: !MAJOR!.!MINOR!
    goto end
)

if not "!MINOR!"=="12" (
    echo Python 3.12 is required. Found: !MAJOR!.!MINOR!
    goto end
)

:: --- Check for CUDA 12.8 ---
echo Checking for CUDA 12.8 installation...
where nvcc >nul 2>&1
if errorlevel 1 (
    echo CUDA Toolkit not found in PATH. Please install CUDA 12.8.
    goto end
)

nvcc --version > temp_cuda.txt
findstr "release 12.8" temp_cuda.txt >nul
if errorlevel 1 (
    echo CUDA 12.8 not found. Please ensure CUDA 12.8 is installed.
    del temp_cuda.txt
    goto end
)
del temp_cuda.txt

echo.
echo All environment checks passed.
echo.

:: --- Ask user to confirm before proceeding ---
set /p USER_CONFIRM=Proceed with ComfyUI installation? (Y/N): 
if /I not "!USER_CONFIRM!"=="Y" (
    echo Installation aborted by user.
    goto end
)

echo.
echo Starting installation...

:: --- Clone ComfyUI repo ---
git clone https://github.com/comfyanonymous/ComfyUI
if errorlevel 1 goto error

cd ComfyUI

:: --- Create venv ---
python -m venv venv
if errorlevel 1 goto error

:: --- Activate venv ---
call venv\Scripts\activate.bat

:: --- Install PyTorch (CUDA 12.8, nightly) ---
pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128
if errorlevel 1 goto error

:: --- Clone ComfyUI-Manager ---
cd custom_nodes
git clone https://github.com/Comfy-Org/ComfyUI-Manager
if errorlevel 1 goto error

cd ComfyUI-Manager
pip install -r requirements.txt
if errorlevel 1 goto error

cd ..\..
pip install -r requirements.txt
if errorlevel 1 goto error

:: --- Launch ComfyUI ---
python main.py
goto end

:error
echo.
echo An error occurred. Please check the messages above.
pause

:end
endlocal
