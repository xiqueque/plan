@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "PYTHON_EXE=C:\Users\Junhong\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
set "PYTHONW_EXE=C:\Users\Junhong\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\pythonw.exe"

if exist "%PYTHONW_EXE%" (
    "%PYTHONW_EXE%" "%~dp0app\main.py"
) else (
    if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"
    where python >nul 2>&1
    if errorlevel 1 (
        echo 未找到 Python 运行环境，请先安装 Python 3.10 或更高版本。
        pause
        exit /b 1
    )
    "%PYTHON_EXE%" -m app.main
)

if errorlevel 1 pause
