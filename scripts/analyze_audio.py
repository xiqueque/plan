"""分析音频：解码 mp3，找到首个有声位置与结尾，用于裁切。"""
from __future__ import annotations

import struct
import sys
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import QEventLoop, QTimer, QUrl  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtMultimedia import QAudioDecoder, QAudioFormat  # noqa: E402

SRC = Path(r"C:\Users\Junhong\Music\8月7日.mp3")
OUT = Path(__file__).resolve().parent.parent / "app" / "assets" / "8月7日_裁剪.wav"
WINDOW_SEC = 0.005  # 5ms 分析窗口
THRESHOLD = 0.04  # 幅度阈值
HEAD_PAD_SEC = 0.02  # 起点前保留
TAIL_PAD_SEC = 0.10  # 结尾后保留


def _samples_from_buffer(buffer) -> list:
    fmt = buffer.format()
    channels = fmt.channelCount()
    data = bytes(buffer.data())
    sample_format = fmt.sampleFormat()
    if sample_format == QAudioFormat.SampleFormat.Int16:
        size = 2
        unpack = lambda b: struct.unpack("<h", b)[0] / 32768.0
    elif sample_format == QAudioFormat.SampleFormat.Float:
        size = 4
        unpack = lambda b: struct.unpack("<f", b)[0]
    elif sample_format == QAudioFormat.SampleFormat.Int32:
        size = 4
        unpack = lambda b: struct.unpack("<i", b)[0] / 2147483648.0
    else:
        raise ValueError(f"不支持的采样格式：{sample_format}")
    frames = len(data) // (size * channels)
    values = []
    for i in range(frames):
        vals = [
            unpack(data[(i * channels + ch) * size:(i * channels + ch + 1) * size])
            for ch in range(channels)
        ]
        values.append(sum(vals) / channels)
    return values


def main() -> None:
    app = QGuiApplication(sys.argv)
    decoder = QAudioDecoder()
    decoder.setSource(QUrl.fromLocalFile(str(SRC)))

    buffers = []
    errors = []
    loop = QEventLoop()

    def on_buffer() -> None:
        buf = decoder.read()
        if buf.isValid():
            buffers.append(buf)

    def on_error(err) -> None:
        errors.append(str(err))
        loop.quit()

    decoder.bufferReady.connect(on_buffer)
    decoder.finished.connect(loop.quit)
    decoder.error.connect(on_error)
    decoder.start()
    QTimer.singleShot(20000, loop.quit)
    loop.exec()

    if errors or not buffers:
        print("解码失败：", errors or "无数据")
        sys.exit(1)

    sample_rate = buffers[0].format().sampleRate()
    samples = []
    for buf in buffers:
        samples.extend(_samples_from_buffer(buf))

    window = max(1, int(sample_rate * WINDOW_SEC))
    peaks = []
    for i in range(0, len(samples), window):
        chunk = samples[i:i + window]
        peaks.append(max(abs(v) for v in chunk) if chunk else 0.0)

    onset_idx = next(
        (i for i, p in enumerate(peaks) if p >= THRESHOLD), len(peaks) - 1
    )
    last_idx = len(peaks) - 1
    for i in range(len(peaks) - 1, -1, -1):
        if peaks[i] >= THRESHOLD:
            last_idx = i
            break

    onset_sec = onset_idx * window / sample_rate
    end_sec = (last_idx + 1) * window / sample_rate
    duration = len(samples) / sample_rate
    print(f"时长：{duration:.2f}s；首个有声：{onset_sec:.3f}s；最后有声：{end_sec:.3f}s")

    start = max(0, onset_sec - HEAD_PAD_SEC)
    end = min(duration, end_sec + TAIL_PAD_SEC)
    s0 = int(start * sample_rate)
    s1 = int(end * sample_rate)
    trimmed = samples[s0:s1]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUT), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        frames = bytearray()
        for v in trimmed:
            frames += struct.pack("<h", int(max(-1.0, min(1.0, v)) * 32767))
        w.writeframes(bytes(frames))
    print(f"已生成裁剪版：{OUT}（{len(trimmed) / sample_rate:.2f}s，起点 {start:.3f}s）")


if __name__ == "__main__":
    main()
