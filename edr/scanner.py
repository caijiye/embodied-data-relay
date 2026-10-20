from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import Config
from .db import Database

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _dir_bytes(path: Path) -> int:
    total = 0
    for p in path.rglob("*"):
        if p.is_file():
            try:
                total += p.stat().st_size
            except OSError:
                pass
    return total


def _count_frames(camera_dir: Path) -> int:
    frames = camera_dir / "frames"
    if frames.is_dir():
        return sum(1 for p in frames.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES)
    for video in camera_dir.glob("video.*"):
        if video.is_file():
            return 1
    return 0


def _camera_dirs(episode_dir: Path) -> list[Path]:
    return sorted(
        [p for p in episode_dir.iterdir() if p.is_dir() and p.name.startswith("camera_")],
        key=lambda p: p.name,
    )


def _is_complete(session_dir: Path, cfg: Config) -> bool:
    marker = session_dir / "_COMPLETE"
    if marker.exists():
        return True
    if cfg.scanner.require_complete_marker:
        return False
    newest = max((p.stat().st_mtime for p in session_dir.rglob("*") if p.is_file()), default=0)
    return (time.time() - newest) >= cfg.scanner.settle_seconds


def scan_incoming(cfg: Config, db: Database) -> list[str]:
    ready: list[str] = []
    for session_dir in sorted(p for p in cfg.paths.incoming.iterdir() if p.is_dir()):
        if session_dir.name.startswith("."):
            continue
        if not _is_complete(session_dir, cfg):
            age = time.time() - max(
                (p.stat().st_mtime for p in session_dir.rglob("*") if p.is_file()), default=time.time()
            )
            if age > cfg.scanner.settle_seconds * 3:
                db.add_event(
                    "warn",
                    "scanner",
                    f"session incomplete: {session_dir.name}",
                    {"path": str(session_dir)},
                )
            continue

        symlinks = [p for p in session_dir.rglob("*") if p.is_symlink()]
        if session_dir.is_symlink() or symlinks:
            db.add_event(
                "error",
                "scanner",
                f"session rejected: symlinks are not allowed",
                {"path": str(session_dir), "count": len(symlinks)},
            )
            continue

        meta = _read_json(session_dir / "meta.json")
        raw_bytes = _dir_bytes(session_dir)
        marker = session_dir / "_COMPLETE"
        completed_at = datetime.fromtimestamp(
            marker.stat().st_mtime if marker.exists() else session_dir.stat().st_mtime,
            tz=timezone.utc,
        ).isoformat()

        session_id = db.upsert_session(
            name=session_dir.name,
            path=str(session_dir),
            robot_id=meta.get("robot_id"),
            site=meta.get("site"),
            task=meta.get("task"),
            started_at=meta.get("started_at"),
            completed_at=completed_at,
            status="ready",
            raw_bytes=raw_bytes,
        )

        episode_dirs = sorted(
            [p for p in session_dir.iterdir() if p.is_dir() and p.name.startswith("episode_")],
            key=lambda p: p.name,
        )
        for episode_dir in episode_dirs:
            ep_meta = _read_json(episode_dir / "meta.json")
            cameras = _camera_dirs(episode_dir)
            if not cameras:
                cameras = [p for p in episode_dir.glob("*.mp4")]
            frame_count = sum(_count_frames(c) if c.is_dir() else 0 for c in cameras)
            db.upsert_episode(
                session_id=session_id,
                name=episode_dir.name,
                path=str(episode_dir),
                camera_count=len(cameras),
                frame_count=frame_count,
                raw_bytes=_dir_bytes(episode_dir),
                status="discovered",
            )
        db.update_session_bytes(session_id)
        ready.append(session_dir.name)
        db.add_event("info", "scanner", f"session ready: {session_dir.name}", {"episodes": len(episode_dirs)})
    return ready
