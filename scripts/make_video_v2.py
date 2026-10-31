# -*- coding: utf-8 -*-
"""Clip-based demo video: one TTS audio per subtitle, exact duration sync."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import subprocess
import time
import wave
from datetime import datetime, timezone
from http.client import HTTPSConnection
from pathlib import Path

BASE = Path(r"D:\MyProject\开放原子")
SLIDES = BASE / "data" / "video" / "slides"
OUT = BASE / "data" / "video" / "v2"
CLIP_AUDIO = OUT / "clips"
SEG = OUT / "segments"
for p in (OUT, CLIP_AUDIO, SEG):
    p.mkdir(parents=True, exist_ok=True)

VOICE = 402002
MODEL = 1
SR = 24000
PRE = 0.25
GAP = 0.18
SCENE_GAP = 0.45
TAIL = 0.35

# (clip id, scene, tts text, subtitle text with \N line break)
CLIPS = [
    ("c01", "01_cover", "具身数据驿，一套放在采集现场的边缘数据站。", "具身数据驿，\\N一套放在采集现场的边缘数据站。"),
    ("c02", "01_cover", "它把原始 TB，变成可训练小时。", "它把原始 TB，\\N变成可训练小时。"),
    ("c03", "02_problem", "具身数据一天就是 TB 级。", "具身数据一天就是 TB 级。"),
    ("c04", "02_problem", "八路 1080p 原始画面，每秒约 1.5 GB；", "八路 1080p 原始画面，\\N每秒约 1.5 GB；"),
    ("c05", "02_problem", "1 TB 走 10 Mbps，要 9 天。", "1 TB 走 10 Mbps，\\N要 9 天。"),
    ("c06", "02_problem", "而原始素材，大约只有三成能真正用于训练。", "而原始素材，\\N大约只有三成能真正用于训练。"),
    ("c07", "03_solution", "我们在采集现场做五件事：", "我们在采集现场做五件事："),
    ("c08", "03_solution", "会话感知写入、质量门禁、H.264 减量、NVMe 与 HDD 分层、可恢复交付。", "会话感知写入、质量门禁、H.264 减量、\\NNVMe 与 HDD 分层、可恢复交付。"),
    ("c09", "03_solution", "质量门禁只隔离，不删除；训练端按片段取用。", "质量门禁只隔离，不删除；\\N训练端按片段取用。"),
    ("c10", "04_demo1", "这是实际跑出来的 dashboard。", "这是实际跑出来的 dashboard。"),
    ("c11", "04_demo1", "原始数据 48.6 MB，训练就绪 239.7 KB，减量 99.5%。", "原始数据 48.6 MB，\\N训练就绪 239.7 KB，减量 99.5%。"),
    ("c12", "04_demo1", "交付延迟 0.0 小时，数据到训练的时间，被压到现场。", "交付延迟 0.0 小时，\\N数据到训练的时间，被压到现场。"),
    ("c13", "05_demo2", "质量门禁给出 2 个 pass、1 个 review、4 个 quarantine。", "质量门禁给出 2 个 pass、\\N1 个 review、4 个 quarantine。"),
    ("c14", "05_demo2", "热层保留 3 个片段，4 个还在待处理。", "热层保留 3 个片段，\\N4 个还在待处理。"),
    ("c15", "05_demo2", "交付队列按质量优先，失败自动重试。", "交付队列按质量优先，\\N失败自动重试。"),
    ("c16", "06_benchmark", "10 Mbps 上行，端到端从 123.9 秒降到 9.2 秒，加速 13.53 倍。", "10 Mbps 上行，端到端从 123.9 秒\\N降到 9.2 秒，加速 13.53 倍。"),
    ("c17", "06_benchmark", "真实开源样本，427 KB 压到 66 KB，减量 84.6%。", "真实开源样本，\\N427 KB 压到 66 KB，减量 84.6%。"),
    ("c18", "06_benchmark", "99.3% 是合成数据上界，我们不把它当真实世界数字。", "99.3% 是合成数据上界，\\N我们不把它当真实世界数字。"),
    ("c19", "07_hardware", "整机约 3,453 元，18 TB，折合每 TB 192 元。", "整机约 3,453 元，18 TB，\\N折合每 TB 192 元。"),
    ("c20", "07_hardware", "USB 3.0 实测约 400 MB/s，单块 HDD 顺序 200 到 260 MB/s。", "USB 3.0 实测约 400 MB/s，\\N单块 HDD 顺序 200 到 260 MB/s。"),
    ("c21", "07_hardware", "BOM、接线、外壳、固件全部开源。", "BOM、接线、外壳、\\N固件全部开源。"),
    ("c22", "08_open", "软件 Apache 2.0，硬件 CERN-OHL-S，文档 CC BY 4.0。", "软件 Apache 2.0，\\N硬件 CERN-OHL-S，文档 CC BY 4.0。"),
    ("c23", "08_open", "12 个 pytest，GitHub Actions 持续集成。", "12 个 pytest，\\NGitHub Actions 持续集成。"),
    ("c24", "08_open", "别人可以照着 BOM，装出同一台设备。", "别人可以照着 BOM，\\N装出同一台设备。"),
    ("c25", "09_close", "让数据在采集现场，就变少、变可用、变得可交付。", "让数据在采集现场，\\N就变少、变可用、变得可交付。"),
    ("c26", "09_close", "具身数据驿，期待在开源社区见面。", "具身数据驿，\\N期待在开源社区见面。"),
]


def sign(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def tts(text: str, out: Path) -> None:
    sid = os.environ["TENCENTCLOUD_SECRET_ID"]
    skey = os.environ["TENCENTCLOUD_SECRET_KEY"]
    host, action, version = "tts.tencentcloudapi.com", "TextToVoice", "2019-08-23"
    payload = json.dumps({
        "Text": text, "SessionId": out.stem, "VoiceType": VOICE,
        "Volume": 0, "Speed": 0, "ProjectId": 0, "ModelType": MODEL,
        "PrimaryLanguage": 1, "SampleRate": SR, "Codec": "mp3",
    }, ensure_ascii=False, separators=(",", ":"))
    ts = int(time.time())
    date = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
    ct = "application/json; charset=utf-8"
    ch = f"content-type:{ct}\nhost:{host}\nx-tc-action:{action.lower()}\n"
    sh = "content-type;host;x-tc-action"
    cr = "\n".join(["POST", "/", "", ch, sh, hashlib.sha256(payload.encode()).hexdigest()])
    scope = f"{date}/tts/tc3_request"
    sts = "\n".join(["TC3-HMAC-SHA256", str(ts), scope, hashlib.sha256(cr.encode()).hexdigest()])
    kd = sign(("TC3" + skey).encode(), date)
    ks = sign(kd, "tts")
    ksign = sign(ks, "tc3_request")
    sig = hmac.new(ksign, sts.encode(), hashlib.sha256).hexdigest()
    auth = f"TC3-HMAC-SHA256 Credential={sid}/{scope}, SignedHeaders={sh}, Signature={sig}"
    headers = {
        "Authorization": auth, "Content-Type": ct, "Host": host,
        "X-TC-Action": action, "X-TC-Timestamp": str(ts), "X-TC-Version": version,
    }
    conn = HTTPSConnection(host, timeout=90)
    conn.request("POST", "/", headers=headers, body=payload.encode())
    body = json.loads(conn.getresponse().read().decode("utf-8", errors="replace"))
    resp = body.get("Response", {})
    if "Error" in resp:
        raise RuntimeError(resp["Error"])
    out.write_bytes(base64.b64decode(resp["Audio"]))


def to_wav(src: Path, dst: Path) -> float:
    # trim leading/trailing silence so the measured duration is the spoken clip
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-i", str(src),
        "-af", "silenceremove=start_periods=1:start_duration=0.04:start_threshold=-45dB,"
               "areverse,silenceremove=start_periods=1:start_duration=0.08:start_threshold=-45dB,areverse",
        "-ar", "48000", "-ac", "1", "-sample_fmt", "s16", str(dst),
    ], check=True)
    with wave.open(str(dst), "rb") as w:
        return w.getnframes() / w.getframerate()


def ts(sec: float) -> str:
    cs = int(round(sec * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def build_timeline() -> dict:
    rows = []
    cursor = PRE
    prev_scene = None
    for cid, scene, text, sub in CLIPS:
        mp3 = CLIP_AUDIO / f"{cid}.mp3"
        wav = CLIP_AUDIO / f"{cid}.wav"
        if not mp3.exists():
            for attempt in range(1, 4):
                try:
                    print("tts", cid, "attempt", attempt, text[:24])
                    tts(text, mp3)
                    break
                except Exception as exc:
                    print("retry", cid, type(exc).__name__, exc)
                    if attempt == 3:
                        raise
                    time.sleep(2)
        dur = to_wav(mp3, wav)
        if prev_scene is not None:
            cursor += SCENE_GAP if scene != prev_scene else GAP
        rows.append({
            "id": cid, "scene": scene, "text": text, "sub": sub,
            "audio": str(wav), "start": round(cursor, 3),
            "end": round(cursor + dur, 3), "duration": round(dur, 3),
        })
        cursor += dur
        prev_scene = scene
    total = cursor + TAIL

    # narration WAV
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

    # scene boundaries
    scenes = []
    for r in rows:
        if not scenes or scenes[-1]["scene"] != r["scene"]:
            scenes.append({"scene": r["scene"], "start": r["start"], "clips": []})
        scenes[-1]["clips"].append(r["id"])
    for i, s in enumerate(scenes):
        s["end"] = scenes[i + 1]["start"] if i + 1 < len(scenes) else total
        s["duration"] = round(s["end"] - s["start"], 3)

    # ASS
    ass = [
        "[Script Info]", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080",
        "WrapStyle: 0", "ScaledBorderAndShadow: yes", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Sub,Microsoft YaHei,46,&H00FFFFFF,&H000000FF,&H00101820,&H80000000,1,0,0,0,100,100,0,0,1,3,1,2,80,80,46,1",
        "", "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for r in rows:
        end = min(r["end"] + 0.05, r["end"] + GAP - 0.02)
        ass.append(f"Dialogue: 0,{ts(r['start'])},{ts(end)},Sub,,0,0,0,,{r['sub']}")
    (OUT / "subtitles.ass").write_text("\n".join(ass) + "\n", encoding="utf-8")

    data = {"voice": VOICE, "total": round(total, 3), "clips": rows, "scenes": scenes}
    (OUT / "timeline.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("total", total, "clips", len(rows))
    for s in scenes:
        print(s["scene"], s["start"], s["duration"])
    return data


def render(data: dict) -> None:
    segments = []
    n = len(data["scenes"])
    for i, s in enumerate(data["scenes"], 1):
        slide = SLIDES / f"{s['scene']}.png"
        seg = SEG / f"{i:02d}_{s['scene']}.mp4"
        vf = "scale=1920:1080,format=yuv420p"
        if i == 1:
            vf += ",fade=t=in:st=0:d=0.3"
        if i == n:
            vf += f",fade=t=out:st={max(0, s['duration'] - 0.4):.3f}:d=0.4"
        subprocess.run([
            "ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", "30",
            "-i", str(slide), "-t", f"{s['duration']:.3f}", "-vf", vf, "-r", "30",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-pix_fmt", "yuv420p", "-an", str(seg),
        ], check=True)
        segments.append(seg)
    lst = SEG / "list.txt"
    lst.write_text("\n".join(f"file '{p.name}'" for p in segments), encoding="utf-8")
    out = OUT / "demo.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
        "-i", str(OUT / "narration.wav"),
        "-vf", "subtitles=subtitles.ass",
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest",
        "-movflags", "+faststart", str(out),
    ], check=True, cwd=str(OUT))
    print("saved", out)


if __name__ == "__main__":
    data = build_timeline()
    render(data)
