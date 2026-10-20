from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from edr.config import Config, DeliveryConfig, PathsConfig, ScannerConfig, TieringConfig
from edr.db import Database
from edr.pipeline import run_pipeline
from tests.conftest import make_session


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
def test_pipeline_packages_and_delivers(tmp_path):
    incoming = tmp_path / "incoming"
    make_session(incoming, "session_test", ["sharp", "black"])

    cfg = Config(
        base_dir=tmp_path,
        paths=PathsConfig(
            incoming=incoming,
            hot=tmp_path / "hot",
            cold=tmp_path / "cold",
            quarantine=tmp_path / "quarantine",
            db=tmp_path / "edr.db",
            logs=tmp_path / "logs",
        ),
        scanner=ScannerConfig(settle_seconds=0, require_complete_marker=True),
        tiering=TieringConfig(hot_sessions=1, auto_tier=True),
        delivery=DeliveryConfig(enabled=True, target="local", local_dir=tmp_path / "delivered"),
    )
    cfg.ensure_dirs()
    db = Database(cfg.paths.db)

    summary = run_pipeline(cfg, db)
    assert summary["packaged"] == 1
    assert summary["quarantined"] == 1
    assert summary["delivered"] == 1
    assert summary["errors"] == 0

    stats = db.stats()
    assert stats["episodes"] == 2
    assert stats["compact_bytes"] > 0
    assert stats["statuses"].get("delivered") == 1
    assert stats["statuses"].get("quarantined") == 1

    sessions = db.list_sessions()
    assert sessions[0]["status"] == "completed"
    assert Path(sessions[0]["path"]).exists()

    delivered = list((tmp_path / "delivered").rglob("*.mp4"))
    assert delivered, "expected compacted camera files in delivery target"
