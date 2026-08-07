"""合成内置音效：勾选完成时的可爱短促弹跳音（无版权素材）。"""
from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "app" / "assets"
SAMPLE_RATE = 44100


def tone(freq: float, start_sec: float, dur_sec: float, volume: float = 0.85) -> list:
    """生成一个带指数衰减包络的正弦音。"""
    samples = []
    n = int(SAMPLE_RATE * dur_sec)
    for i in range(n):
        t = i / SAMPLE_RATE
        envelope = math.exp(-t * 14)
        samples.append(volume * envelope * math.sin(2 * math.pi * freq * (start_sec + t)))
    return samples


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    # 可爱的上行两连音（类似弹跳“叮-咚”）
    s1 = tone(740, 0.0, 0.10, 0.85)
    s2 = tone(988, 0.08, 0.16, 0.85)
    total = max(len(s1), len(s2))

    mixed = []
    for i in range(total):
        v = (s1[i] if i < len(s1) else 0.0) + (s2[i] if i < len(s2) else 0.0)
        mixed.append(v)

    # 归一化到接近满音量，避免叠加后削波失真
    peak = max(1e-6, max(abs(v) for v in mixed))
    scale = 0.96 / peak
    buf = bytearray()
    for v in mixed:
        buf += struct.pack("<h", int(max(-1.0, min(1.0, v * scale)) * 32767))

    out = ASSETS / "check.wav"
    with wave.open(str(out), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(bytes(buf))
    print(f"音效已生成：{out}（{total / SAMPLE_RATE:.2f} 秒）")


if __name__ == "__main__":
    main()
