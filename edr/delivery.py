from __future__ import annotations

import json
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import Config
from .db import Database


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _copy_local(src: Path, dst: Path) -> int:
    dst.mkdir(parents=True, exist_ok=True)
    total = 0
    for p in sorted(src.rglob("*")):
        if not p.is_file():
            continue
        target = dst / p.relative_to(src)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, target)
        total += p.stat().st_size
    return total


def _upload_s3(src: Path, cfg: Config, session: str, episode: str) -> tuple[int, int]:
    import boto3
    from botocore.config import Config as BotoConfig

    client = boto3.client(
        "s3",
        endpoint_url=cfg.delivery.endpoint,
        aws_access_key_id=cfg.delivery.access_key,
        aws_secret_access_key=cfg.delivery.secret_key,
        region_name=cfg.delivery.region,
        config=BotoConfig(signature_version="s3v4", s3={"addressing_style": "path"}),
    )
    bucket = cfg.delivery.bucket
    try:
        client.head_bucket(Bucket=bucket)
    except Exception:
        client.create_bucket(Bucket=bucket)

    checkpoint_path = src / ".delivered.json"
    checkpoint: dict[str, Any] = {"keys": []}
    if checkpoint_path.exists():
        try:
            checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            checkpoint = {"keys": []}
    uploaded = set(checkpoint.get("keys", []))

    total = 0
    attempts = 0
    for p in sorted(src.rglob("*")):
        if not p.is_file() or p.name == ".delivered.json":
            continue
        rel = p.relative_to(src).as_posix()
        key = f"{cfg.delivery.prefix}/{session}/{episode}/{rel}"
        if key in uploaded:
            continue
        for attempt in range(1, cfg.delivery.max_attempts + 1):
            try:
                client.upload_file(str(p), bucket, key)
                break
            except Exception:
                attempts += 1
                if attempt >= cfg.delivery.max_attempts:
                    raise
                time.sleep(2 ** attempt)
        uploaded.add(key)
        total += p.stat().st_size
        checkpoint["keys"] = sorted(uploaded)
        checkpoint_path.write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2), encoding="utf-8")
    return total, attempts


def deliver_episode(cfg: Config, db: Database, episode: dict[str, Any]) -> dict[str, Any]:
    target = cfg.delivery.target if cfg.delivery.enabled else "disabled"
    delivery_id = db.create_delivery(int(episode["id"]), target)
    started = _utcnow()
    db.update_delivery(delivery_id, status="running", started_at=started)

    if not cfg.delivery.enabled:
        db.update_delivery(delivery_id, status="skipped", finished_at=_utcnow())
        return {"status": "skipped", "bytes": 0, "attempts": 0, "error": None}

    package_path = episode.get("package_path")
    if not package_path:
        error = "episode has no package_path"
        db.update_delivery(delivery_id, status="failed", error=error, finished_at=_utcnow())
        return {"status": "failed", "bytes": 0, "attempts": 0, "error": error}

    src = Path(package_path)
    if not src.exists():
        error = f"package missing: {src}"
        db.update_delivery(delivery_id, status="failed", error=error, finished_at=_utcnow())
        return {"status": "failed", "bytes": 0, "attempts": 0, "error": error}

    try:
        if target == "local":
            dst = cfg.delivery.local_dir / episode["session_name"] / episode["name"]
            uploaded = _copy_local(src, dst)
            attempts = 0
        elif target == "s3":
            uploaded, attempts = _upload_s3(src, cfg, episode["session_name"], episode["name"])
        else:
            raise ValueError(f"unknown delivery target: {target}")
    except Exception as exc:
        error = str(exc)
        db.update_delivery(
            delivery_id, status="failed", error=error, finished_at=_utcnow(), attempts=1
        )
        db.add_event("error", "delivery", f"delivery failed: {episode['name']}", {"error": error})
        return {"status": "failed", "bytes": 0, "attempts": 1, "error": error}

    finished = _utcnow()
    db.update_delivery(
        delivery_id,
        status="delivered",
        bytes_uploaded=uploaded,
        attempts=attempts,
        finished_at=finished,
    )
    db.set_episode_status(int(episode["id"]), "delivered")
    db.add_event(
        "info",
        "delivery",
        f"delivered: {episode['session_name']}/{episode['name']}",
        {"bytes": uploaded, "target": target},
    )
    return {"status": "delivered", "bytes": uploaded, "attempts": attempts, "error": None}


def deliver_pending(cfg: Config, db: Database, limit: int = 1000) -> dict[str, int]:
    counts = {"delivered": 0, "failed": 0, "skipped": 0}
    for episode in db.list_episodes(status="packaged", limit=limit):
        result = deliver_episode(cfg, db, episode)
        counts[result["status"]] = counts.get(result["status"], 0) + 1
    return counts
