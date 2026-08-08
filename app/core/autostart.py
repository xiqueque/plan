"""开机自启动：通过当前用户注册表 Run 键管理。"""
from __future__ import annotations

import sys
import winreg
from pathlib import Path

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "每日计划"


def _command() -> str:
    """生成启动命令：pythonw + 入口脚本绝对路径（不依赖当前目录）。"""
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    python = Path(sys.executable)
    if python.name.lower() == "python.exe":
        python = python.with_name("pythonw.exe")
    main_script = Path(__file__).resolve().parent.parent / "main.py"
    return f'"{python}" "{main_script}"'


def is_enabled() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            winreg.QueryValueEx(key, APP_NAME)
            return True
    except FileNotFoundError:
        return False
    except OSError:
        return False


def enable() -> None:
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
    ) as key:
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, _command())


def disable() -> None:
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.DeleteValue(key, APP_NAME)
    except FileNotFoundError:
        pass


def create_desktop_shortcut() -> bool:
    """在桌面创建指向当前程序的快捷方式（供首次运行的新用户使用）。"""
    try:
        import subprocess

        exe = sys.executable
        ps = (
            "$ws = New-Object -ComObject WScript.Shell; "
            "$desktop = [Environment]::GetFolderPath('Desktop'); "
            "$lnk = $ws.CreateShortcut((Join-Path $desktop '每日计划.lnk')); "
            f"$lnk.TargetPath = '{exe}'; "
            f"$lnk.WorkingDirectory = '{Path(exe).parent}'; "
            f"$lnk.IconLocation = '{exe}'; "
            "$lnk.Save()"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            check=False,
            creationflags=0x08000000,  # CREATE_NO_WINDOW
            timeout=30,
        )
        return True
    except Exception:
        return False
