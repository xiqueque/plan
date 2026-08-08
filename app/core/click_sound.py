"""按键交互提示音：优先使用随程序自带的裁剪版（去掉开头静音）。"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl

_TRIMMED = Path(__file__).resolve().parent.parent / "assets" / "8月8日_裁剪.wav"
CLICK_SOUND = (
    _TRIMMED
    if _TRIMMED.exists()
    else Path(r"C:\Users\Junhong\Music\8月8日.mp3")
)

_player = None
_audio = None


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
    # mp3 等格式：Qt 多媒体播放（可靠、可控音量）
    global _player, _audio
    try:
        from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

        if _player is None:
            _player = QMediaPlayer()
            _audio = QAudioOutput()
            _audio.setVolume(0.55)
            _player.setAudioOutput(_audio)
        _player.stop()
        _player.setSource(QUrl.fromLocalFile(str(CLICK_SOUND)))
        _player.play()
        return
    except Exception:
        pass
    # 兜底：系统 MCI 播放
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
