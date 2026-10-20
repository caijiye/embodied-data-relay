from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import TranscodeConfig

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
TEXT_SUFFIXES = {".json", ".jsonl", ".yaml", ".yml", ".txt", ".csv"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run(cmd: list[str], cfg: TranscodeConfig) -> None:
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    except FileNotFoundError as exc:
        raise RuntimeError(f"ffmpeg not found: {cfg.ffmpeg}") from exc
    except subprocess.CalledProcessError as exc:
        tail = (exc.stderr or "")[-2000:]
        raise RuntimeError(f"ffmpeg failed ({exc.returncode}): {' '.join(cmd)}\n{tail}") from exc


def _transcode_frames(frames_dir: Path, out_file: Path, cfg: TranscodeConfig) -> bool:
    images = sorted(p for p in frames_dir.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES)
    if not images:
        return False

    first = images[0]
    pattern_match = re.fullmatch(r"(\d{6})(\.[A-Za-z0-9]+)", first.name)
    if pattern_match:
        pattern = f"%06d{pattern_match.group(2)}"
        cmd = [
            cfg.ffmpeg,
            "-y",
            "-framerate",
            str(cfg.fps),
            "-i",
            (frames_dir / pattern).as_posix(),
            "-c:v",
            cfg.video_codec,
            "-preset",
            cfg.preset,
            "-crf",
            str(cfg.crf),
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(out_file),
        ]
        _run(cmd, cfg)
        return True

    with tempfile.TemporaryDirectory(prefix="edr-concat-") as tmp:
        list_file = Path(tmp) / "frames.txt"
        lines: list[str] = []
        duration = 1.0 / max(cfg.fps, 1)
        for image in images:
            safe = image.as_posix().replace("'", "'\\''")
            lines.append(f"file '{safe}'")
            lines.append(f"duration {duration:.6f}")
        last_safe = images[-1].as_posix().replace("'", "'\\''")
        lines.append(f"file '{last_safe}'")
        list_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        cmd = [
            cfg.ffmpeg,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_file),
            "-r",
            str(cfg.fps),
            "-c:v",
            cfg.video_codec,
            "-preset",
            cfg.preset,
            "-crf",
            str(cfg.crf),
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(out_file),
        ]
        _run(cmd, cfg)
    return True


def _transcode_video(video: Path, out_file: Path, cfg: TranscodeConfig) -> bool:
    cmd = [
        cfg.ffmpeg,
        "-y",
        "-i",
        str(video),
        "-an",
        "-c:v",
        cfg.video_codec,
        "-preset",
        cfg.preset,
        "-crf",
        str(cfg.crf),
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(out_file),
    ]
    _run(cmd, cfg)
    return True


def _dir_bytes(path: Path) -> int:
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def _copy_metadata(episode_dir: Path, out_dir: Path) -> None:
    for p in episode_dir.iterdir():
        if p.is_file() and p.suffix.lower() in TEXT_SUFFIXES:
            shutil.copy2(p, out_dir / p.name)


def compact_episode(
    episode_dir: Path,
    out_dir: Path,
    cfg: TranscodeConfig,
    quality_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    camera_dirs = sorted(
        [p for p in episode_dir.iterdir() if p.is_dir() and p.name.startswith("camera_")],
        key=lambda p: p.name,
    )
    if not camera_dirs:
        camera_dirs = []

    transcoded: list[str] = []
    for camera in camera_dirs:
        out_file = out_dir / f"{camera.name}.mp4"
        frames_dir = camera / "frames"
        if frames_dir.is_dir() and _transcode_frames(frames_dir, out_file, cfg):
            transcoded.append(out_file.name)
            continue
        videos = sorted(camera.glob("video.*"))
        if videos and _transcode_video(videos[0], out_file, cfg):
            transcoded.append(out_file.name)
            continue

    if not transcoded:
        for video in sorted(episode_dir.glob("*.mp4")):
            out_file = out_dir / f"{video.stem}.mp4"
            if _transcode_video(video, out_file, cfg):
                transcoded.append(out_file.name)

    if not transcoded:
        raise RuntimeError(f"no transcodable camera data in {episode_dir}")

    _copy_metadata(episode_dir, out_dir)

    raw_bytes = _dir_bytes(episode_dir)
    files: list[dict[str, Any]] = []
    for p in sorted(out_dir.rglob("*")):
        if p.is_file():
            files.append(
                {
                    "path": p.relative_to(out_dir).as_posix(),
                    "bytes": p.stat().st_size,
                    "sha256": _sha256(p),
                }
            )
    compact_bytes = sum(f["bytes"] for f in files)
    manifest = {
        "episode": episode_dir.name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": str(episode_dir),
        "output": str(out_dir),
        "cameras": transcoded,
        "files": files,
        "raw_bytes": raw_bytes,
        "compact_bytes": compact_bytes,
        "reduction_ratio": round(1 - compact_bytes / raw_bytes, 4) if raw_bytes else 0.0,
        "quality": quality_report or {},
    }
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest
