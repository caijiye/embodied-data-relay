# -*- coding: utf-8 -*-
"""Generate Tencent TTS narration and a timeline for the EDR demo video.

Credentials must be supplied via TENCENTCLOUD_SECRET_ID / TENCENTCLOUD_SECRET_KEY.
"""

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
AUDIO = BASE / "data" / "video" / "audio"
AUDIO.mkdir(parents=True, exist_ok=True)

VOICE = 402002
MODEL = 1
SAMPLE_RATE = 24000
PRE = 0.45
POST = 0.65

SCENES = [
    ("01_cover", "具身数据驿，一套放在采集现场的边缘数据站。它把原始 TB，变成可训练小时。"),
    ("02_problem", "具身数据一天就是 TB 级。八路 1080p 原始画面，每秒约 1.5 GB；1 TB 走 10 Mbps，要 9 天。而原始素材，大约只有三成能真正用于训练。"),
    ("03_solution", "我们在采集现场做五件事：会话感知写入、质量门禁、H.264 减量、NVMe 与 HDD 分层、可恢复交付。质量门禁只隔离，不删除；训练端按片段取用。"),
    ("04_demo1", "这是实际跑出来的 dashboard。原始数据 48.6 MB，训练就绪 239.7 KB，减量 99.5%。交付延迟 0.0 小时，数据到训练的时间，被压到现场。"),
    ("05_demo2", "质量门禁给出 2 个 pass、1 个 review、4 个 quarantine。热层保留 3 个片段，4 个还在待处理。交付队列按质量优先，失败自动重试。"),
    ("06_benchmark", "10 Mbps 上行，端到端从 123.9 秒降到 9.2 秒，加速 13.53 倍。真实开源样本，427 KB 压到 66 KB，减量 84.6%。99.3% 是合成数据上界，我们不把它当真实世界数字。"),
    ("07_hardware", "整机约 3,453 元，18 TB，折合每 TB 192 元。USB 3.0 实测约 400 MB/s，单块 HDD 顺序 200 到 260 MB/s。BOM、接线、外壳、固件全部开源。"),
    ("08_open", "软件 Apache 2.0，硬件 CERN-OHL-S，文档 CC BY 4.0。12 个 pytest，GitHub Actions 持续集成。别人可以照着 BOM，装出同一台设备。"),
    ("09_close", "让数据在采集现场，就变少、变可用、变得可交付。具身数据驿，期待在开源社区见面。"),
]


def sign(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def tts(text: str, out: Path) -> None:
    sid = os.environ["TENCENTCLOUD_SECRET_ID"]
    skey = os.environ["TENCENTCLOUD_SECRET_KEY"]
    host, action, version = "tts.tencentcloudapi.com", "TextToVoice", "2019-08-23"
    payload = json.dumps({
        "Text": text,
        "SessionId": out.stem,
        "VoiceType": VOICE,
        "Volume": 0,
        "Speed": 0,
        "ProjectId": 0,
        "ModelType": MODEL,
        "PrimaryLanguage": 1,
        "SampleRate": SAMPLE_RATE,
        "Codec": "mp3",
    }, ensure_ascii=False, separators=(",", ":"))

    ts = int(time.time())
    date = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
    ct = "application/json; charset=utf-8"
    canonical_headers = f"content-type:{ct}\nhost:{host}\nx-tc-action:{action.lower()}\n"
    signed_headers = "content-type;host;x-tc-action"
    hashed_payload = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    canonical_request = "\n".join(["POST", "/", "", canonical_headers, signed_headers, hashed_payload])
    scope = f"{date}/tts/tc3_request"
    string_to_sign = "\n".join([
        "TC3-HMAC-SHA256", str(ts), scope,
        hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
    ])
    kd = sign(("TC3" + skey).encode("utf-8"), date)
    ks = sign(kd, "tts")
    ksign = sign(ks, "tc3_request")
    signature = hmac.new(ksign, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
    auth = f"TC3-HMAC-SHA256 Credential={sid}/{scope}, SignedHeaders={signed_headers}, Signature={signature}"
    headers = {
        "Authorization": auth, "Content-Type": ct, "Host": host,
        "X-TC-Action": action, "X-TC-Timestamp": str(ts), "X-TC-Version": version,
    }
    conn = HTTPSConnection(host, timeout=60)
    conn.request("POST", "/", headers=headers, body=payload.encode("utf-8"))
    resp = conn.getresponse()
    data = json.loads(resp.read().decode("utf-8", errors="replace")).get("Response", {})
    if "Error" in data:
        raise RuntimeError(data["Error"])
    out.write_bytes(base64.b64decode(data["Audio"]))


def to_wav(src: Path, dst: Path) -> None:
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-i", str(src),
        "-ar", "48000", "-ac", "1", "-sample_fmt", "s16", str(dst),
    ], check=True)


def main() -> None:
    wav_paths = []
    for name, text in SCENES:
        mp3 = AUDIO / f"{name}.mp3"
        wav = AUDIO / f"{name}.wav"
        if not mp3.exists():
            print("tts", name)
            tts(text, mp3)
        to_wav(mp3, wav)
        with wave.open(str(wav), "rb") as w:
            dur = w.getnframes() / w.getframerate()
        wav_paths.append((name, wav, dur))
        print(f"{name}: {dur:.2f}s")

    # concatenate with silence, all 48k mono s16
    out_wav = AUDIO / "narration.wav"
    timeline = []
    cursor = 0.0
    with wave.open(str(out_wav), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(48000)
        for name, wav, dur in wav_paths:
            pre = int(PRE * 48000)
            post = int(POST * 48000)
            out.writeframes(b"\x00\x00" * pre)
            with wave.open(str(wav), "rb") as w:
                out.writeframes(w.readframes(w.getnframes()))
            out.writeframes(b"\x00\x00" * post)
            total = PRE + dur + POST
            timeline.append({
                "scene": name,
                "start": round(cursor, 3),
                "duration": round(total, 3),
                "audio_start": round(cursor + PRE, 3),
                "audio_duration": round(dur, 3),
            })
            cursor += total

    (AUDIO / "timeline.json").write_text(
        json.dumps({"voice": VOICE, "total": round(cursor, 3), "scenes": timeline},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"total {cursor:.2f}s -> {out_wav}")


if __name__ == "__main__":
    main()
