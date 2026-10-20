from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import Config
from .db import Database
from .delivery import deliver_pending
from .quality import analyze_episode
from .scanner import scan_incoming
from .tiering import tier_episodes
from .transcode import compact_episode


def run_pipeline(cfg: Config, db: Database, limit: int = 1000) -> dict[str, Any]:
    ready = scan_incoming(cfg, db)
    summary: dict[str, Any] = {
        "sessions_ready": len(ready),
        "quality_checked": 0,
        "packaged": 0,
        "quarantined": 0,
        "incomplete": 0,
        "errors": 0,
    }

    for episode in db.list_episodes(status="discovered", limit=limit):
        episode_dir = Path(episode["path"])
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

            out_dir = cfg.paths.hot / episode["session_name"] / episode["name"]
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
            db.set_episode_status(int(episode["id"]), "error")
            db.add_event(
                "error",
                "pipeline",
                f"episode failed: {episode['name']}",
                {"error": str(exc)},
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
