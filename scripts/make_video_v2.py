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
OUT = BASE / "data" / "video" / "v3"
CLIP_AUDIO = OUT / "clips"
SEG = OUT / "segments"
for p in (OUT, CLIP_AUDIO, SEG):
    p.mkdir(parents=True, exist_ok=True)

VOICE = 402002
MODEL = 1
SR = 24000
PRE = 0.25
GAP = 0.3
SCENE_GAP = 0.3
TAIL = 0.35

# (clip id, scene, tts text, subtitle text with \N line break)
CLIPS = [
    ('c01', '01_cover', '具身数据驿，一套放在采集现场的边缘数据站。它把原始 T B，变成可训练小时。', '具身数据驿，一套放在采集现场的边缘数据站。', '它把原始 TB，变成可训练小时。'),
    ('c02', '02_problem', '具身数据一天就是 T B 级。八路一零八零 P 原始画面，每秒约一点五 G B；', '具身数据一天就是 TB 级。', '八路 1080p 原始画面，每秒约 1.5 GB；'),
    ('c03', '02_problem', '一 T B 走十兆比特每秒，要九天。而原始素材，大约只有三成能真正用于训练。', '1 TB 走 10 Mbps，要 9 天。', '而原始素材，大约只有三成能真正用于训练。'),
    ('c04', '03_solution', '我们在采集现场做五件事：会话感知写入、质量门禁、H点二六四减量。', '我们在采集现场做五件事：会话感知写入、', '质量门禁、H.264 减量。'),
    ('c05', '03_solution', 'N V M E 与 H D D 分层、可恢复交付。质量门禁只隔离，不删除；训练端按片段取用。', 'NVMe 与 HDD 分层、可恢复交付。', '质量门禁只隔离，不删除；训练端按片段取用。'),
    ('c06', '04_demo1', '这是实际跑出来的 dashboard。原始数据四十八点六 M B，训练就绪二百三十九点七 K B，减量百分之九十九点五。', '这是实际跑出来的 dashboard。', '原始数据 48.6 MB，训练就绪 239.7 KB，减量 99.5%。'),
    ('c07', '04_demo1', '交付延迟零点零小时，数据到训练的时间，被压到现场。', '交付延迟 0.0 小时，', '数据到训练的时间，被压到现场。'),
    ('c08', '05_demo2', '质量门禁给出两个 pass、一个 review、四个 quarantine。', '质量门禁给出 2 个 pass、', '1 个 review、4 个 quarantine。'),
    ('c09', '05_demo2', '热层保留三个片段，四个还在待处理。交付队列按质量优先，失败自动重试。', '热层保留 3 个片段，4 个还在待处理。', '交付队列按质量优先，失败自动重试。'),
    ('c10', '06_benchmark', '十兆比特每秒上行，端到端从一百二十三点九秒降到九点二秒，加速十三点五三倍。', '10 Mbps 上行，端到端从 123.9 秒', '降到 9.2 秒，加速 13.53 倍。'),
    ('c11', '06_benchmark', '真实开源样本，四百二十七 K B 压到六十六 K B，减量百分之八十四点六。', '真实开源样本，427 KB 压到 66 KB，减量 84.6%。', ''),
    ('c12', '06_benchmark', '百分之九十九点三是合成数据上界，我们不把它当真实世界数字。', '99.3% 是合成数据上界，', '我们不把它当真实世界数字。'),
    ('c13', '07_hardware', '整机约三千四百五十三元，十八 T B，折合每 T B 一百九十二元。', '整机约 3,453 元，18 TB，', '折合每 TB 192 元。'),
    ('c14', '07_hardware', 'USB 三点零实测约四百兆字节每秒，单块 H D D 顺序两百到两百六十兆字节每秒。', 'USB 3.0 实测约 400 MB/s，', '单块 HDD 顺序 200 到 260 MB/s。'),
    ('c15', '07_hardware', 'B O M、接线、外壳、固件全部开源。', 'BOM、接线、外壳、', '固件全部开源。'),
    ('c16', '08_open', '软件 Apache 二点零，硬件 C E R N O H L S，文档 C C B Y 四点零。', '软件 Apache 2.0，', '硬件 CERN-OHL-S，文档 CC BY 4.0。'),
    ('c17', '08_open', '十二个 pytest，GitHub Actions 持续集成。别人可以照着 B O M，装出同一台设备。', '12 个 pytest，GitHub Actions 持续集成。', '别人可以照着 BOM，装出同一台设备。'),
    ('c18', '09_close', '让数据在采集现场，就变少、变可用、变得可交付。', '让数据在采集现场，', '就变少、变可用、变得可交付。'),
    ('c19', '09_close', '具身数据驿，期待在开源社区见面。', '具身数据驿，', '期待在开源社区见面。'),
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
    # keep the TTS output as-is: no trimming, no silence removal
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-i", str(src),
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
    for cid, scene, tts_text, line1, line2 in CLIPS:
        sub = line1 if not line2 else line1 + chr(92) + "N" + line2
        mp3 = CLIP_AUDIO / f"{cid}.mp3"
        wav = CLIP_AUDIO / f"{cid}.wav"
        if not mp3.exists():
            for attempt in range(1, 4):
                try:
                    print("tts", cid, "attempt", attempt, tts_text[:24])
                    tts(tts_text, mp3)
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
            "id": cid, "scene": scene, "text": tts_text, "sub": sub,
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
