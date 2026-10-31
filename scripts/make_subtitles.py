# -*- coding: utf-8 -*-
"""Build ASS/SRT subtitles from the narration timeline and speech pauses."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

BASE = Path(r"D:\MyProject\开放原子")
AUDIO = BASE / "data" / "video" / "audio"
OUT = BASE / "data" / "video"

# (scene, chunk text with \N line break, first_segment, last_segment)
CHUNKS = {
    "01_cover": [
        ("具身数据驿，\\N一套放在采集现场的边缘数据站。", 0, 1),
        ("它把原始 TB，\\N变成可训练小时。", 2, 3),
    ],
    "02_problem": [
        ("具身数据一天就是 TB 级。", 0, 1),
        ("八路 1080p 原始画面，\\N每秒约 1.5 GB；", 2, 3),
        ("1 TB 走 10 Mbps，\\N要 9 天。", 4, 5),
        ("而原始素材，\\N大约只有三成能真正用于训练。", 6, 6),
    ],
    "03_solution": [
        ("我们在采集现场做五件事：", 0, 0),
        ("会话感知写入、质量门禁、\\NH.264 减量、", 1, 3),
        ("NVMe 与 HDD 分层、\\N可恢复交付。", 4, 5),
        ("质量门禁只隔离，不删除；", 6, 7),
        ("训练端按片段取用。", 8, 10),
    ],
    "04_demo1": [
        ("这是实际跑出来的 dashboard。", 0, 0),
        ("原始数据 48.6 MB，\\N训练就绪 239.7 KB，减量 99.5%。", 1, 2),
        ("交付延迟 0.0 小时，", 3, 3),
        ("数据到训练的时间，\\N被压到现场。", 4, 5),
    ],
    "05_demo2": [
        ("质量门禁给出 2 个 pass、\\N1 个 review、4 个 quarantine。", 0, 2),
        ("热层保留 3 个片段，\\N4 个还在待处理。", 3, 4),
        ("交付队列按质量优先，\\N失败自动重试。", 5, 6),
    ],
    "06_benchmark": [
        ("10 Mbps 上行，端到端从 123.9 秒\\N降到 9.2 秒，加速 13.53 倍。", 0, 2),
        ("真实开源样本，\\N427 KB 压到 66 KB，减量 84.6%。", 3, 4),
        ("99.3% 是合成数据上界，", 5, 5),
        ("我们不把它当真实世界数字。", 6, 8),
    ],
    "07_hardware": [
        ("整机约 3,453 元，18 TB，\\N折合每 TB 192 元。", 0, 2),
        ("USB 3.0 实测约 400 MB/s，", 3, 3),
        ("单块 HDD 顺序 200 到 260 MB/s。", 4, 4),
        ("BOM、接线、外壳、\\N固件全部开源。", 5, 8),
    ],
    "08_open": [
        ("软件 Apache 2.0，", 0, 1),
        ("硬件 CERN-OHL-S，\\N文档 CC BY 4.0。", 2, 4),
        ("12 个 pytest，\\NGitHub Actions 持续集成。", 5, 7),
        ("别人可以照着 BOM，", 8, 8),
        ("装出同一台设备。", 9, 10),
    ],
    "09_close": [
        ("让数据在采集现场，", 0, 0),
        ("就变少、变可用、\\N变得可交付。", 1, 3),
        ("具身数据驿，\\N期待在开源社区见面。", 4, 5),
    ],
}


def speech_segments(wav: Path) -> list[tuple[float, float]]:
    p = subprocess.run([
        "ffmpeg", "-hide_banner", "-i", str(wav),
        "-af", "silencedetect=noise=-35dB:d=0.18", "-f", "null", "-",
    ], capture_output=True, text=True, encoding="utf-8", errors="replace")
    txt = p.stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", txt)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", txt)]
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", txt)
    dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
    sil = list(zip(starts, ends + [dur]))
    speech: list[tuple[float, float]] = []
    prev = 0.0
    for s, e in sil:
        if s > prev + 0.15:
            speech.append((prev, s))
        prev = max(prev, e)
    if prev < dur - 0.15:
        speech.append((prev, dur))
    return speech


def ts(sec: float) -> str:
    cs = int(round(sec * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def srt_ts(sec: float) -> str:
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main() -> None:
    timeline = json.loads((AUDIO / "timeline.json").read_text(encoding="utf-8"))
    scenes = {s["scene"]: s for s in timeline["scenes"]}
    events = []
    for scene, chunks in CHUNKS.items():
        speech = speech_segments(AUDIO / f"{scene}.wav")
        info = scenes[scene]
        for text, a, b in chunks:
            start = info["audio_start"] + speech[a][0]
            end = info["audio_start"] + speech[b][1]
            events.append((start, end, text))
        print(scene, "speech", len(speech), "chunks", len(chunks))
    events.sort()

    ass = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1920",
        "PlayResY: 1080",
        "WrapStyle: 0",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Sub,Microsoft YaHei,46,&H00FFFFFF,&H000000FF,&H00101820,&H80000000,1,0,0,0,100,100,0,0,1,3,1,2,80,80,46,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for start, end, text in events:
        ass.append(f"Dialogue: 0,{ts(start)},{ts(end)},Sub,,0,0,0,,{text}")
    (OUT / "subtitles.ass").write_text("\n".join(ass) + "\n", encoding="utf-8")

    srt = []
    for i, (start, end, text) in enumerate(events, 1):
        srt.append(f"{i}\n{srt_ts(start)} --> {srt_ts(end)}\n{text.replace(chr(92)+'N', chr(10))}\n")
    (OUT / "subtitles.srt").write_text("\n".join(srt), encoding="utf-8")
    print("events", len(events), "->", OUT / "subtitles.ass")


if __name__ == "__main__":
    main()
