from __future__ import annotations

import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from .config import QualityConfig

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}


def _sample_images(frames_dir: Path, max_frames: int) -> list[np.ndarray]:
    paths = sorted(p for p in frames_dir.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES)
    if not paths:
        return []
    if len(paths) <= max_frames:
        chosen = paths
    else:
        step = max(1, len(paths) // max_frames)
        chosen = paths[::step][:max_frames]
    frames: list[np.ndarray] = []
    for path in chosen:
        try:
            buf = np.fromfile(str(path), dtype=np.uint8)
            img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
        except (OSError, ValueError):
            img = None
        if img is not None:
            frames.append(img)
    return frames


def _sample_video(video: Path, max_frames: int) -> list[np.ndarray]:
    cap = cv2.VideoCapture(str(video))
    tmpdir: Path | None = None
    if not cap.isOpened():
        cap.release()
        tmpdir = Path(tempfile.mkdtemp(prefix="edr-video-"))
        tmp_video = tmpdir / ("video" + video.suffix)
        shutil.copy2(video, tmp_video)
        cap = cv2.VideoCapture(str(tmp_video))
    if not cap.isOpened():
        cap.release()
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)
        return []
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    frames: list[np.ndarray] = []
    if total <= 0:
        ok, frame = cap.read()
        if ok:
            frames.append(frame)
    else:
        if total <= max_frames:
            indices = list(range(total))
        else:
            step = max(1, total // max_frames)
            indices = list(range(0, total, step))[:max_frames]
        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ok, frame = cap.read()
            if ok:
                frames.append(frame)
    cap.release()
    if tmpdir:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return frames


def _camera_metrics(frames: list[np.ndarray], cfg: QualityConfig) -> dict[str, Any]:
    if not frames:
        return {
            "sampled": 0,
            "mean_blur": 0.0,
            "min_blur": 0.0,
            "mean_brightness": 0.0,
            "black_ratio": 1.0,
            "duplicate_ratio": 0.0,
            "score": 0.0,
            "reasons": ["no frames"],
        }

    blurs: list[float] = []
    brightness: list[float] = []
    black_flags: list[bool] = []
    duplicate_count = 0
    pairs = 0
    prev_gray: np.ndarray | None = None
    for frame in frames:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurs.append(float(cv2.Laplacian(gray, cv2.CV_64F).var()))
        mean = float(gray.mean())
        brightness.append(mean)
        black_flags.append(mean < 5.0)
        if prev_gray is not None:
            diff = float(np.mean(cv2.absdiff(prev_gray, gray)))
            if diff < 0.1:
                duplicate_count += 1
            pairs += 1
        prev_gray = gray

    mean_blur = float(np.mean(blurs))
    min_blur = float(np.min(blurs))
    mean_brightness = float(np.mean(brightness))
    black_ratio = float(np.mean(black_flags))
    duplicate_ratio = duplicate_count / pairs if pairs else 0.0

    blur_score = min(100.0, mean_blur / max(cfg.blur_threshold, 1e-6) * 100.0)
    if cfg.dark_threshold <= mean_brightness <= cfg.bright_threshold:
        exposure_score = 100.0
    else:
        distance = min(
            abs(mean_brightness - cfg.dark_threshold),
            abs(mean_brightness - cfg.bright_threshold),
        )
        exposure_score = max(0.0, 100.0 - distance * 2.0)
    black_score = max(0.0, 100.0 - black_ratio / max(cfg.black_frame_threshold, 1e-6) * 100.0)
    dup_score = max(0.0, 100.0 - duplicate_ratio / max(cfg.duplicate_threshold, 1e-6) * 100.0)

    score = 0.40 * blur_score + 0.25 * exposure_score + 0.20 * black_score + 0.15 * dup_score
    reasons: list[str] = []
    if mean_blur < cfg.blur_threshold:
        reasons.append("blur")
    if mean_brightness < cfg.dark_threshold:
        reasons.append("dark")
    if mean_brightness > cfg.bright_threshold:
        reasons.append("bright")
    if black_ratio > cfg.black_frame_threshold:
        reasons.append("black_frames")
    if duplicate_ratio > cfg.duplicate_threshold:
        reasons.append("duplicate_frames")

    return {
        "sampled": len(frames),
        "mean_blur": round(mean_blur, 2),
        "min_blur": round(min_blur, 2),
        "mean_brightness": round(mean_brightness, 2),
        "black_ratio": round(black_ratio, 3),
        "duplicate_ratio": round(duplicate_ratio, 3),
        "score": round(score, 1),
        "reasons": reasons,
    }


def analyze_episode(episode_dir: Path, cfg: QualityConfig) -> dict[str, Any]:
    camera_dirs = sorted(
        [p for p in episode_dir.iterdir() if p.is_dir() and p.name.startswith("camera_")],
        key=lambda p: p.name,
    )
    if not camera_dirs:
        camera_dirs = [p for p in episode_dir.glob("*.mp4")]

    cameras: dict[str, Any] = {}
    reasons: list[str] = []
    hard_quarantine = False
    total_sampled = 0

    for camera in camera_dirs:
        if camera.is_dir():
            frames_dir = camera / "frames"
            if frames_dir.is_dir():
                frames = _sample_images(frames_dir, cfg.sample_frames)
            else:
                videos = sorted(camera.glob("video.*"))
                frames = _sample_video(videos[0], cfg.sample_frames) if videos else []
        else:
            frames = _sample_video(camera, cfg.sample_frames)

        metrics = _camera_metrics(frames, cfg)
        cameras[camera.name] = metrics
        total_sampled += metrics["sampled"]
        for reason in metrics["reasons"]:
            tag = f"{camera.name}:{reason}"
            if tag not in reasons:
                reasons.append(tag)
        if metrics["black_ratio"] > cfg.black_frame_threshold:
            hard_quarantine = True
        if metrics["mean_blur"] < cfg.blur_threshold * 0.5:
            hard_quarantine = True
        if metrics["duplicate_ratio"] > 0.8:
            hard_quarantine = True

    if not cameras:
        return {
            "score": 0.0,
            "status": "incomplete",
            "reasons": ["no cameras"],
            "cameras": {},
            "sampled_frames": 0,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        }

    score = float(np.mean([c["score"] for c in cameras.values()]))
    if any(c["sampled"] == 0 for c in cameras.values()):
        status = "incomplete"
    elif hard_quarantine or score < cfg.quarantine_score:
        status = "quarantine"
    elif score < cfg.review_score or reasons:
        status = "review"
    else:
        status = "pass"

    return {
        "score": round(score, 1),
        "status": status,
        "reasons": reasons,
        "cameras": cameras,
        "sampled_frames": total_sampled,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }
