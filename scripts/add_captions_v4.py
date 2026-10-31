# -*- coding: utf-8 -*-
"""Burn page-level captions into the 7-page video (no audio splitting)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

BASE = Path(r"D:\MyProject\开放原子")
SRC = BASE / "data" / "video" / "v4"
OUT = BASE / "data" / "video" / "v6"
OUT.mkdir(parents=True, exist_ok=True)

CAPTIONS = {
    "01_cover": [
        "具身数据驿，是一套放在具身数据采集现场的存储方案。",
        "它用 SSD 和 HDD 分工，在尽量不损失速度的前提下，",
        "降低每 TB 的存储成本。",
        "下面先从采集端的数据压力说起。",
    ],
    "02_problem": [
        "先看采集端。八路 1080p 画面，原始写入速度约 1.5 GB/s；",
        "1 TB 数据通过 10 Mbps 上行回传，需要约 9 天。",
        "与此同时，原始素材中只有约三成能真正进入训练。",
        "采集端不处理，存储和回传成本会被无效数据放大。",
    ],
    "03_cost_problem": [
        "现有方案通常直接用全闪存或云存储。",
        "以 18 TB 为例，全闪存仅介质成本约 ¥9,081；",
        "云存储首年约 ¥25,920。",
        "对大规模采集来说，这个成本很难持续。",
    ],
    "04_design": [
        "采集时，数据先写入 SSD，保证写入和读取速度。",
        "会话结束后，系统检查画面质量，压缩可用片段，",
        "再将历史数据迁移到 HDD。",
        "常用数据留 SSD，历史数据进 HDD，热路径仍由 SSD 承担。",
    ],
    "05_speed": [
        "USB 3.0 实测约 400 MB/s，",
        "单块 HDD 顺序读写约 200–260 MB/s。",
        "接口带宽高于磁盘本身，HDD 不会成为热路径的瓶颈；",
        "交付和训练读取仍然发生在 SSD 上。",
    ],
    "06_results": [
        "10 Mbps 上行下，数据到训练时间从 123.9 秒降到 9.2 秒，",
        "约 13.5 倍。真实样本从 427 KB 压缩到 66 KB，减量 84.6%。",
        "演示节点 48.6 MB 原始数据生成 239.7 KB 训练包，",
        "交付延迟 0.0 h。",
    ],
    "07_cost": [
        "同样 18 TB，SSD + HDD 混合方案约 ¥3,453，折合 ¥192/TB；",
        "全闪存 ¥9,081（¥505/TB）；",
        "云存储首年 ¥25,920（¥1,440/TB/年）。",
        "混合约为全闪的 38%、云首年的 13%。先存得下，再谈训练。",
    ],
}


def ts(sec: float) -> str:
    cs = int(round(sec * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def main() -> None:
    timeline = json.loads((SRC / "timeline.json").read_text(encoding="utf-8"))
    ass = [
        "[Script Info]", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080",
        "WrapStyle: 0", "ScaledBorderAndShadow: yes", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Cap,Microsoft YaHei,32,&H00111827,&H000000FF,&H00FFFFFF,&H00FFFFFF,1,0,0,0,100,100,0,0,1,1,0,2,80,80,8,1",
        "", "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for p in timeline["pages"]:
        lines = CAPTIONS[p["name"]]
        text = (chr(92) + "N").join(lines)
        start = p["start"] + 0.15
        end = p["start"] + p["duration"] - 0.15
        ass.append(f"Dialogue: 0,{ts(start)},{ts(end)},Cap,,0,0,0,,{text}")
    (OUT / "captions.ass").write_text("\n".join(ass) + "\n", encoding="utf-8")

    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-i", str(SRC / "demo.mp4"),
        "-vf",
        "drawbox=x=0:y=880:w=1920:h=200:color=white@0.94:t=fill,"
        "drawbox=x=0:y=880:w=1920:h=2:color=0xD1D5DB@0.9:t=fill,"
        "subtitles=captions.ass",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "copy", "-movflags", "+faststart", str(OUT / "demo.mp4"),
    ], check=True, cwd=str(OUT))
    print("saved", OUT / "demo.mp4")


if __name__ == "__main__":
    main()
