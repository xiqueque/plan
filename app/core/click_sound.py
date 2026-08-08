"""按键交互提示音：使用昨天同款可爱音效（8月7日_裁剪.wav），默认音量 15%。"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl

_CUTE = Path(__file__).resolve().parent.parent / "assets" / "8月7日_裁剪.wav"
_TRIMMED_8_8 = Path(__file__).resolve().parent.parent / "assets" / "8月8日_裁剪.wav"
CLICK_SOUND = (
    _CUTE
    if _CUTE.exists()
    else (_TRIMMED_8_8 if _TRIMMED_8_8.exists() else Path(r"C:\Users\Junhong\Music\8月7日.mp3"))
)
VOLUME = 0.15

_player = None
_audio = None


def play_click_sound() -> None:
    if not CLICK_SOUND.exists():
        return
    # Qt 多媒体播放（支持 wav/mp3，可控音量）
    global _player, _audio
    try:
        from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

        if _player is None:
            _player = QMediaPlayer()
            _audio = QAudioOutput()
            _audio.setVolume(VOLUME)
            _player.setAudioOutput(_audio)
        _player.stop()
        _player.setSource(QUrl.fromLocalFile(str(CLICK_SOUND)))
        _player.play()
        return
    except Exception:
        pass
    # 兜底：wav 用系统播放
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
