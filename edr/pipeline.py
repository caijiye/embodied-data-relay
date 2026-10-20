from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from filelock import FileLock, Timeout

from .config import Config
from .db import Database
from .delivery import deliver_pending
from .quality import analyze_episode
from .scanner import scan_incoming
from .tiering import tier_episodes
from .transcode import compact_episode


def run_pipeline(cfg: Config, db: Database, limit: int = 1000) -> dict[str, Any]:
    lock = FileLock(str(cfg.paths.db) + ".lock", timeout=0)
    try:
        lock.acquire()
    except Timeout:
        return {"locked": True, "message": "another pipeline is already running"}
    try:
        return _run_pipeline(cfg, db, limit)
    finally:
        lock.release()


def _run_pipeline(cfg: Config, db: Database, limit: int) -> dict[str, Any]:
    ready = scan_incoming(cfg, db)
    summary: dict[str, Any] = {
        "locked": False,
        "sessions_ready": len(ready),
        "quality_checked": 0,
        "packaged": 0,
        "quarantined": 0,
        "incomplete": 0,
        "retried": 0,
        "errors": 0,
    }

    for episode in db.list_episodes_for_processing(cfg.pipeline.max_attempts, limit=limit):
        episode_dir = Path(episode["path"])
        if int(episode.get("attempts") or 0) > 0:
            summary["retried"] += 1
        try:
            report = analyze_episode(episode_dir, cfg.quality)
            db.update_episode_quality(int(episode["id"]), report)
            summary["quality_checked"] += 1

            if report["status"] == "incomplete":
                db.set_episode_status(int(episode["id"]), "incomplete")
                db.add_event(
                    "warn",
                    "quality",
                    f"incomplete episode: {episode['name']}",
                    {"reasons": report.get("reasons", [])},
                )
                summary["incomplete"] += 1
                continue

            if report["status"] == "quarantine":
                db.set_episode_status(int(episode["id"]), "quarantined")
                db.add_event(
                    "warn",
                    "quality",
                    f"quarantined: {episode['session_name']}/{episode['name']}",
                    {"score": report["score"], "reasons": report.get("reasons", [])},
                )
                summary["quarantined"] += 1
                continue

            free = shutil.disk_usage(str(cfg.paths.hot)).free
            required = int(cfg.pipeline.min_free_gb * (1024**3))
            if free < required:
                raise RuntimeError(
                    f"insufficient free space on hot tier: {free / 1e9:.2f} GB < {cfg.pipeline.min_free_gb} GB"
                )

            out_dir = cfg.paths.hot / episode["session_name"] / episode["name"]
            if out_dir.exists():
                shutil.rmtree(out_dir)
            manifest = compact_episode(episode_dir, out_dir, cfg.transcode, report)
            db.update_episode_package(int(episode["id"]), str(out_dir), int(manifest["compact_bytes"]), manifest)
            db.add_event(
                "info",
                "transcode",
                f"packaged: {episode['session_name']}/{episode['name']}",
                {
                    "raw_bytes": manifest["raw_bytes"],
                    "compact_bytes": manifest["compact_bytes"],
                    "reduction_ratio": manifest["reduction_ratio"],
                },
            )
            summary["packaged"] += 1
        except Exception as exc:
            status, attempts = db.mark_episode_error(
                int(episode["id"]), str(exc), cfg.pipeline.max_attempts
            )
            db.add_event(
                "error",
                "pipeline",
                f"episode failed: {episode['name']} "
                f"(attempt {attempts}/{cfg.pipeline.max_attempts}, {status})",
                {"error": str(exc), "episode_id": int(episode["id"])},
            )
            summary["errors"] += 1

    if cfg.delivery.enabled:
        delivery_counts = deliver_pending(cfg, db, limit=limit)
        summary["delivered"] = delivery_counts.get("delivered", 0)
        summary["delivery_failed"] = delivery_counts.get("failed", 0)
        summary["errors"] += delivery_counts.get("failed", 0)
    else:
        summary["delivered"] = 0

    tier_summary = tier_episodes(cfg, db)
    summary["tiered_to_cold"] = tier_summary["moved"]
    db.refresh_session_rollups()
    return summary
