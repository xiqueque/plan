@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "PYTHON_EXE=C:\Users\Junhong\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%PYTHON_EXE%" goto :run

set "PYTHON_EXE=python"
where python >nul 2>&1
if errorlevel 1 (
    echo 未找到 Python 运行环境，请先安装 Python 3.10 或更高版本。
    pause
    exit /b 1
)

:run
"%PYTHON_EXE%" -m app.main
if errorlevel 1 pause
