from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from .config import Config
from .db import Database


def _hot_session_ids(cfg: Config, db: Database) -> set[int]:
    sessions = db.list_sessions(limit=max(cfg.tiering.hot_sessions, 1))
    return {int(s["id"]) for s in sessions[: cfg.tiering.hot_sessions]}


def tier_episodes(cfg: Config, db: Database) -> dict[str, Any]:
    if not cfg.tiering.auto_tier:
        return {"moved": 0, "hot_sessions": []}

    hot_ids = _hot_session_ids(cfg, db)
    moved = 0
    for ep in db.list_episodes(limit=5000):
        if ep["tier"] != "hot":
            continue
        if int(ep["session_id"]) in hot_ids:
            continue
        if ep["status"] not in {"packaged", "delivered"}:
            continue
        if not ep.get("package_path"):
            continue

        src = Path(ep["package_path"])
        if not src.exists():
            continue
        if cfg.paths.cold in src.parents:
            db.set_episode_tier(int(ep["id"]), "cold", str(src))
            continue

        dst = cfg.paths.cold / ep["session_name"] / ep["name"]
        if dst.exists():
            db.set_episode_tier(int(ep["id"]), "cold", str(dst))
            db.add_event(
                "warn",
                "tiering",
                f"cold target already exists, keeping both: {dst}",
                {"episode": ep["name"]},
            )
            continue

        dst.parent.mkdir(parents=True, exist_ok=True)
        tmp = dst.with_name(dst.name + ".tmp")
        if tmp.exists():
            shutil.rmtree(tmp)
        shutil.copytree(src, tmp)
        tmp.rename(dst)
        shutil.rmtree(src)
        db.set_episode_tier(int(ep["id"]), "cold", str(dst))
        db.add_event("info", "tiering", f"moved to cold: {ep['session_name']}/{ep['name']}", None)
        moved += 1

    return {"moved": moved, "hot_sessions": sorted(hot_ids)}
