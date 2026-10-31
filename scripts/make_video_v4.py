# -*- coding: utf-8 -*-
"""Assemble the 7-page white engineering deck with one TTS clip per page."""

from __future__ import annotations

import json
import subprocess
import wave
from pathlib import Path

import make_video_v2 as base

BASE = Path(r"D:\MyProject\开放原子")
OUT = BASE / "data" / "video" / "v4"
AUDIO = OUT / "audio"
SEG = OUT / "segments"
SLIDES = OUT / "slides"
for p in (AUDIO, SEG):
    p.mkdir(parents=True, exist_ok=True)

PRE = 0.2
GAP = 0.3
TAIL = 0.3

PAGES = [
    ("01_cover", "具身数据驿，是一套放在具身数据采集现场的存储方案。它用 SSD 和 HDD 分工，在尽量不损失速度的前提下，降低每 T B 的存储成本。下面先从采集端的数据压力说起。"),
    ("02_problem", "先看采集端。八路一零八零 P 画面，原始写入速度约一点五 G B 每秒；一 T B 数据通过十兆比特每秒上行回传，需要约九天。与此同时，原始素材中只有约三成能真正进入训练。也就是说，如果采集端不做处理，存储和回传成本会被大量无效数据放大。"),
    ("03_cost_problem", "现有方案通常直接用全闪存或云存储。以十八 T B 为例，全闪存仅介质成本约九千零八十一元；云存储首年约两万五千九百二十元。对大规模采集来说，这个成本很难持续。因此，我们把存储分成 SSD 和 HDD 两层。"),
    ("04_design", "采集时，数据先写入 SSD，保证写入和读取速度。一个采集会话结束后，系统检查画面质量，把可用片段压缩，再将历史数据迁移到 HDD。常用数据留在 SSD，历史数据放在 HDD。这样，热路径仍然由 SSD 承担，HDD 只负责大容量归档。"),
    ("05_speed", "速度方面，USB 三点零实测约四百兆字节每秒，单块 HDD 的顺序读写约两百到两百六十兆字节每秒。接口带宽高于磁盘本身，因此 HDD 不会成为热路径的瓶颈；交付和训练读取仍然发生在 SSD 上。"),
    ("06_results", "实际测试中，十兆比特每秒上行下，数据到训练时间从一百二十三点九秒降到九点二秒，约十三点五倍。真实样本从四百二十七 K B 压缩到六十六 K B，减量百分之八十四点六。演示节点上，四十八点六 M B 原始数据生成二百三十九点七 K B 训练就绪包，交付延迟接近零。"),
    ("07_cost", "成本方面，同样十八 T B，SSD 加 HDD 的混合方案约三千四百五十三元，折合每 T B 一百九十二元；全闪存约九千零八十一元，每 T B 五百零五元；云存储首年约两万五千九百二十元。混合方案约为全闪存的百分之三十八，云存储首年的百分之十三。先存得下，再谈训练。"),
]


def main() -> None:
    rows = []
    cursor = PRE
    for i, (name, text) in enumerate(PAGES):
        mp3 = AUDIO / f"{name}.mp3"
        wav = AUDIO / f"{name}.wav"
        if not mp3.exists():
            for attempt in range(1, 4):
                try:
                    print("tts", name, "attempt", attempt)
                    base.tts(text, mp3)
                    break
                except Exception as exc:
                    print("retry", name, type(exc).__name__, exc)
                    if attempt == 3:
                        raise
        dur = base.to_wav(mp3, wav)
        rows.append({"name": name, "audio": str(wav), "start": round(cursor, 3),
                     "end": round(cursor + dur, 3), "duration": round(dur, 3)})
        cursor += dur + (GAP if i < len(PAGES) - 1 else 0)
    total = cursor + TAIL

    with wave.open(str(OUT / "narration.wav"), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(48000)
        pos = 0.0
        for r in rows:
            target = int(round(r["start"] * 48000))
            out.writeframes(b"\x00\x00" * max(0, target - int(pos * 48000)))
            with wave.open(r["audio"], "rb") as w:
                out.writeframes(w.readframes(w.getnframes()))
            pos = r["end"]
        out.writeframes(b"\x00\x00" * int(round((total - pos) * 48000)))

    # page durations: a slide stays until the next page starts
    pages = []
    for i, r in enumerate(rows):
        start = 0.0 if i == 0 else r["start"] - GAP
        end = rows[i + 1]["start"] - GAP if i + 1 < len(rows) else total
        pages.append({"name": r["name"], "start": round(start, 3), "duration": round(end - start, 3)})
        print(r["name"], r["duration"], "page", round(end - start, 3))
    print("total", round(total, 3))

    segs = []
    for i, p in enumerate(pages, 1):
        seg = SEG / f"{i:02d}_{p['name']}.mp4"
        vf = "scale=1920:1080,format=yuv420p"
        if i == 1:
            vf += ",fade=t=in:st=0:d=0.3"
        if i == len(pages):
            vf += f",fade=t=out:st={max(0, p['duration'] - 0.4):.3f}:d=0.4"
        subprocess.run([
            "ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", "30",
            "-i", str(SLIDES / f"{p['name']}.png"), "-t", f"{p['duration']:.3f}",
            "-vf", vf, "-r", "30", "-c:v", "libx264", "-preset", "medium",
            "-crf", "18", "-pix_fmt", "yuv420p", "-an", str(seg),
        ], check=True)
        segs.append(seg)

    lst = SEG / "list.txt"
    lst.write_text("\n".join(f"file '{s.name}'" for s in segs), encoding="utf-8")
    final = OUT / "demo.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
        "-i", str(OUT / "narration.wav"), "-c:v", "copy",
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest",
        "-movflags", "+faststart", str(final),
    ], check=True)
    (OUT / "timeline.json").write_text(json.dumps({"pages": pages, "total": round(total, 3)},
                                                  ensure_ascii=False, indent=2), encoding="utf-8")
    print("saved", final)


if __name__ == "__main__":
    main()
