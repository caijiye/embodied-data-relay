from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter


def _checkerboard(width: int = 96, height: int = 96) -> np.ndarray:
    yy, xx = np.mgrid[0:height, 0:width]
    board = (((xx // 12) + (yy // 12)) % 2) * 70 + 40
    base = np.stack([board, board, board], axis=-1).astype(np.uint8)
    return base


def write_frames(episode_dir: Path, kind: str, n: int = 6) -> None:
    frames_dir = episode_dir / "camera_front" / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    base = _checkerboard()
    height, width = base.shape[:2]
    for i in range(n):
        if kind == "duplicate":
            frame = base.copy()
        else:
            frame = base.copy()
            x = 8 + i * 4
            frame[height // 2 - 8 : height // 2 + 8, x : x + 16] = 235
        image = Image.fromarray(frame)
        if kind == "blur":
            image = image.filter(ImageFilter.GaussianBlur(radius=10))
        elif kind == "dark":
            image = ImageEnhance.Brightness(image).enhance(0.04)
        elif kind == "bright":
            image = Image.new("RGB", image.size, (255, 255, 255))
        elif kind == "black":
            image = Image.new("RGB", image.size, (0, 0, 0))
        image.save(frames_dir / f"{i:06d}.png", format="PNG")


def make_episode(root: Path, name: str, kind: str = "sharp", frames: int = 6) -> Path:
    episode = root / name
    episode.mkdir(parents=True, exist_ok=True)
    write_frames(episode, kind, frames)
    (episode / "meta.json").write_text(
        json.dumps({"episode": name, "task": "test", "kind": kind}, ensure_ascii=False),
        encoding="utf-8",
    )
    (episode / "state.jsonl").write_text(
        "\n".join(json.dumps({"t": i / 30, "joint_positions": [0] * 7}) for i in range(frames)) + "\n",
        encoding="utf-8",
    )
    return episode


def make_session(root: Path, name: str = "session_test", episodes: list[str] | None = None) -> Path:
    session = root / name
    session.mkdir(parents=True, exist_ok=True)
    (session / "meta.json").write_text(
        json.dumps({"session": name, "robot_id": "test-bot", "site": "test-lab"}, ensure_ascii=False),
        encoding="utf-8",
    )
    for kind in episodes or ["sharp"]:
        make_episode(session, f"episode_{kind}", kind)
    (session / "_COMPLETE").write_text("done\n", encoding="utf-8")
    return session
