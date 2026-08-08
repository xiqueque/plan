"""按键交互提示音：使用 Music 文件夹的 8月8日.mp3。"""
from __future__ import annotations

from pathlib import Path

CLICK_SOUND = Path(r"C:\Users\Junhong\Music\8月8日.mp3")


def play_click_sound() -> None:
    if not CLICK_SOUND.exists():
        return
    # wav 用系统播放
    try:
        import winsound

        if CLICK_SOUND.suffix.lower() == ".wav":
            winsound.PlaySound(
                str(CLICK_SOUND),
                winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT,
            )
            return
    except Exception:
        pass
    # 其他格式（mp3）用系统 MCI 播放
    try:
        import ctypes

        winmm = ctypes.windll.winmm
        alias = "dailyplan_click"
        winmm.mciSendStringW("close " + alias, None, 0, None)
        winmm.mciSendStringW(f'open "{CLICK_SOUND}" alias {alias}', None, 0, None)
        winmm.mciSendStringW(f"setaudio {alias} volume to 500", None, 0, None)
        winmm.mciSendStringW("play " + alias, None, 0, None)
    except Exception:
        pass
