from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from edr.config import (
    Config,
    DeliveryConfig,
    PathsConfig,
    PipelineConfig,
    ScannerConfig,
    TieringConfig,
)
from edr.db import Database
from edr.pipeline import run_pipeline
from tests.conftest import make_session


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
def test_tiering_moves_older_session_to_cold(tmp_path):
    incoming = tmp_path / "incoming"
    make_session(incoming, "session_a", ["sharp"])
    make_session(incoming, "session_b", ["sharp"])

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
        pipeline=PipelineConfig(max_attempts=3, min_free_gb=0.0),
    )
    cfg.ensure_dirs()
    db = Database(cfg.paths.db)

    summary = run_pipeline(cfg, db)
    assert summary["delivered"] == 2
    assert summary["tiered_to_cold"] == 1

    tiers = {episode["session_name"]: episode["tier"] for episode in db.list_episodes()}
    assert tiers["session_a"] == "cold"
    assert tiers["session_b"] == "hot"
    for episode in db.list_episodes():
        assert Path(episode["package_path"]).exists()
        assert episode["status"] == "delivered"
