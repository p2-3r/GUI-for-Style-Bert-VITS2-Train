@echo off
python ./src/init_.py
for /f "delims=" %%A in ('python ./src/read_stylepath.py') do set OUTPUT=%%A

set PYDIR=%~dp0
cd %OUTPUT%

if exist "./venv/Scripts/activate" (
    call "./venv/Scripts/activate"
    echo [34mINFO[0m^|[32m%time:~0,2%:%time:~3,2%:%time:~6,2%[0m^|Running tool...
    python "%PYDIR%main.py"
) else (
    echo [31mERROR[0m: Could not start Style-Bert-VITS2 venv
    pause
    exit
)