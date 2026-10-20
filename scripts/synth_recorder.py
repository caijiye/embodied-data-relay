"""Generate synthetic embodied data collection sessions.

Layout:
  <out>/<session>/_COMPLETE
  <out>/<session>/meta.json
  <out>/<session>/episode_0001/meta.json
  <out>/<session>/episode_0001/state.jsonl
  <out>/<session>/episode_0001/camera_front/frames/000000.png
"""

from __future__ import annotations

import argparse
import json
import math
import random
import shutil
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

CAMERA_NAMES = ["front", "wrist_left", "wrist_right", "overhead"]
TASKS = [
    "pick_and_place",
    "open_drawer",
    "fold_towel",
    "pour_water",
    "insert_peg",
    "wipe_table",
]
DEFECTS = ["normal", "normal", "blur", "dark", "duplicate", "black", "bright"]


def _font(size: int = 16):
    for name in ("arial.ttf", "DejaVuSans.ttf", "simhei.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _draw_frame(
    width: int,
    height: int,
    camera_idx: int,
    frame: int,
    frames: int,
    label: str,
    texture: np.ndarray,
    noise_sigma: float,
    noise_seed: int,
):
    img = Image.new("RGB", (width, height), (18, 24, 30))
    draw = ImageDraw.Draw(img)
    square = max(24, width // 16)
    colors = [(34, 44, 54), (62, 82, 98)]
    for y in range(0, height, square):
        for x in range(0, width, square):
            color = colors[((x // square) + (y // square)) % 2]
            draw.rectangle([x, y, x + square - 1, y + square - 1], fill=color)

    t = frame / max(frames - 1, 1)
    cx = int(50 + t * (width - 100))
    cy = int(height * 0.55 + math.sin(frame / 8.0 + camera_idx) * height * 0.12)
    radius = max(10, int(width * 0.035))
    palette = [(61, 220, 151), (90, 169, 255), (255, 180, 84), (255, 107, 107)]
    color = palette[camera_idx % len(palette)]
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=color)
    draw.line([(int(width * 0.18), int(height * 0.82)), (cx, cy)], fill=(210, 220, 230), width=max(3, width // 120))
    draw.rectangle([int(width * 0.18) - 12, int(height * 0.82) - 12, int(width * 0.18) + 12, int(height * 0.82) + 12], fill=(230, 235, 240))

    font = _font(max(12, width // 40))
    text = f"{label}  F{frame:04d}"
    box = draw.textbbox((0, 0), text, font=font)
    pad = 6
    draw.rectangle([8, 8, 8 + (box[2] - box[0]) + pad * 2, 8 + (box[3] - box[1]) + pad * 2], fill=(5, 8, 12))
    draw.text((8 + pad, 8 + pad - box[1]), text, fill=(230, 238, 246), font=font)

    arr = np.asarray(img, dtype=np.float32)
    arr = arr * 0.88 + texture.astype(np.float32) * 0.12
    if noise_sigma > 0:
        rng = np.random.default_rng(noise_seed)
        arr = arr + rng.normal(0.0, noise_sigma, arr.shape).astype(np.float32)
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def _apply_defect(img: Image.Image, defect: str, frame: int, cached_first: Image.Image | None):
    if defect == "blur":
        return img.filter(ImageFilter.GaussianBlur(radius=8))
    if defect == "dark":
        return ImageEnhance.Brightness(img).enhance(0.06)
    if defect == "bright":
        return ImageEnhance.Brightness(img).enhance(4.0)
    if defect == "duplicate" and cached_first is not None and frame > 0 and frame % 10 != 0:
        return cached_first.copy()
    if defect == "black" and frame % 3 == 0:
        return Image.new("RGB", img.size, (0, 0, 0))
    return img


def generate(
    out: Path,
    sessions: int,
    episodes: int,
    cameras: int,
    frames: int,
    width: int,
    height: int,
    fps: int,
    seed: int,
    clean: bool,
    noise_sigma: float,
) -> dict:
    random.seed(seed)
    if clean and out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    camera_names = CAMERA_NAMES[:cameras]
    if cameras > len(CAMERA_NAMES):
        camera_names += [f"cam_{i}" for i in range(len(CAMERA_NAMES), cameras)]

    textures = []
    for c_idx in range(cameras):
        rng = np.random.default_rng(seed + c_idx * 1009)
        textures.append(rng.integers(0, 256, (height, width, 3), dtype=np.uint8))

    total_bytes = 0
    defect_map: dict[str, str] = {}
    now = datetime.now(timezone.utc)

    for s_idx in range(sessions):
        session_name = f"session_{s_idx + 1:03d}"
        session_dir = out / session_name
        session_dir.mkdir(parents=True, exist_ok=True)
        session_meta = {
            "session": session_name,
            "robot_id": f"robot-{s_idx % 3 + 1:02d}",
            "site": ["beijing-lab", "shenzhen-factory", "hangzhou-home"][s_idx % 3],
            "operator": f"operator-{s_idx % 2 + 1}",
            "started_at": now.isoformat(),
            "fps": fps,
            "width": width,
            "height": height,
            "cameras": camera_names,
        }
        (session_dir / "meta.json").write_text(json.dumps(session_meta, ensure_ascii=False, indent=2), encoding="utf-8")

        for e_idx in range(episodes):
            episode_name = f"episode_{e_idx + 1:04d}"
            episode_dir = session_dir / episode_name
            defect = DEFECTS[(s_idx * episodes + e_idx) % len(DEFECTS)]
            defect_map[f"{session_name}/{episode_name}"] = defect
            episode_dir.mkdir(parents=True, exist_ok=True)
            episode_meta = {
                "episode": episode_name,
                "task": TASKS[(s_idx + e_idx) % len(TASKS)],
                "success": defect != "black",
                "defect": defect,
                "fps": fps,
                "cameras": camera_names,
            }
            (episode_dir / "meta.json").write_text(
                json.dumps(episode_meta, ensure_ascii=False, indent=2), encoding="utf-8"
            )

            with (episode_dir / "state.jsonl").open("w", encoding="utf-8") as fh:
                for frame in range(frames):
                    row = {
                        "t": round(frame / max(fps, 1), 4),
                        "joint_positions": [round(math.sin(frame / 12 + j) * 0.8, 4) for j in range(7)],
                        "gripper": round((math.sin(frame / 10) + 1) / 2, 4),
                    }
                    fh.write(json.dumps(row, ensure_ascii=False) + "\n")

            for c_idx, camera in enumerate(camera_names):
                camera_dir = episode_dir / f"camera_{camera}" / "frames"
                camera_dir.mkdir(parents=True, exist_ok=True)
                cached_first = None
                for frame in range(frames):
                    img = _draw_frame(
                        width,
                        height,
                        c_idx,
                        frame,
                        frames,
                        f"S{s_idx + 1} E{e_idx + 1} C{camera}",
                        textures[c_idx],
                        noise_sigma,
                        seed + s_idx * 100000 + e_idx * 1000 + c_idx * 100 + frame,
                    )
                    if frame == 0:
                        cached_first = img.copy()
                    img = _apply_defect(img, defect, frame, cached_first)
                    path = camera_dir / f"{frame:06d}.png"
                    img.save(path, format="PNG", compress_level=1)

            for p in episode_dir.rglob("*"):
                if p.is_file():
                    total_bytes += p.stat().st_size

        (session_dir / "_COMPLETE").write_text(now.isoformat() + "\n", encoding="utf-8")

    return {
        "sessions": sessions,
        "episodes": sessions * episodes,
        "cameras": cameras,
        "frames": frames,
        "resolution": f"{width}x{height}",
        "defects": defect_map,
        "output": str(out),
        "bytes": total_bytes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate synthetic embodied data collection sessions")
    parser.add_argument("--out", default="data/incoming")
    parser.add_argument("--sessions", type=int, default=3)
    parser.add_argument("--episodes", type=int, default=6)
    parser.add_argument("--cameras", type=int, default=4)
    parser.add_argument("--frames", type=int, default=60)
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--noise", type=float, default=4.0, help="per-frame sensor noise sigma (0 disables)")
    parser.add_argument("--clean", action="store_true", help="remove the output directory first")
    args = parser.parse_args()

    summary = generate(
        out=Path(args.out),
        sessions=args.sessions,
        episodes=args.episodes,
        cameras=args.cameras,
        frames=args.frames,
        width=args.width,
        height=args.height,
        fps=args.fps,
        seed=args.seed,
        clean=args.clean,
        noise_sigma=args.noise,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
