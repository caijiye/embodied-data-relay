# -*- coding: utf-8 -*-
"""Assemble the EDR demo video from slides and the TTS timeline."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

BASE = Path(r"D:\MyProject\开放原子")
SLIDES = BASE / "data" / "video" / "slides"
AUDIO = BASE / "data" / "video" / "audio"
WORK = BASE / "data" / "video" / "segments"
WORK.mkdir(parents=True, exist_ok=True)


def run(cmd):
    print(" ".join(str(c) for c in cmd))
    subprocess.run([str(c) for c in cmd], check=True)


def render(scene: str, dur: float, idx: int, total: int) -> Path:
    slide = SLIDES / f"{scene}.png"
    seg = WORK / f"{idx:02d}_{scene}.mp4"
    vf = "scale=1920:1080,format=yuv420p"
    if idx == 1:
        vf += ",fade=t=in:st=0:d=0.3"
    if idx == total:
        vf += f",fade=t=out:st={max(0, dur - 0.4):.3f}:d=0.4"
    run([
        "ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", "30",
        "-i", slide, "-t", f"{dur:.3f}", "-vf", vf, "-r", "30",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-an", seg,
    ])
    return seg


def build(which: str) -> None:
    data = json.loads((AUDIO / "timeline.json").read_text(encoding="utf-8"))
    all_scenes = data["scenes"]
    scenes = all_scenes[:2] if which == "sample" else all_scenes
    total = len(scenes)
    segments = []
    for i, s in enumerate(scenes, 1):
        dur = s["duration"] + (0.5 if i == total else 0)
        segments.append(render(s["scene"], dur, i, total))

    list_file = WORK / f"list_{which}.txt"
    list_file.write_text("\n".join(f"file '{p.name}'" for p in segments), encoding="utf-8")
    out = BASE / "data" / "video" / ("demo_24s.mp4" if which == "sample" else "demo_full.mp4")
    run([
        "ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
        "-i", list_file, "-i", AUDIO / "narration.wav",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-shortest", "-movflags", "+faststart", out,
    ])
    print("saved", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--which", choices=["sample", "full"], required=True)
    build(ap.parse_args().which)
