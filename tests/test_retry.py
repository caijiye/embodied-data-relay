from __future__ import annotations

import shutil

import pytest

from edr.config import (
    Config,
    DeliveryConfig,
    PathsConfig,
    PipelineConfig,
    ScannerConfig,
    TieringConfig,
    TranscodeConfig,
)
from edr.db import Database
from edr.pipeline import run_pipeline
from tests.conftest import make_session


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
def test_pipeline_retries_after_transcode_error(tmp_path):
    incoming = tmp_path / "incoming"
    make_session(incoming, "session_retry", ["sharp"])

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
        transcode=TranscodeConfig(ffmpeg="nonexistent-ffmpeg", fps=30),
        tiering=TieringConfig(hot_sessions=1, auto_tier=True),
        delivery=DeliveryConfig(enabled=True, target="local", local_dir=tmp_path / "delivered"),
        pipeline=PipelineConfig(max_attempts=3, min_free_gb=0.0),
    )
    cfg.ensure_dirs()
    db = Database(cfg.paths.db)

    first = run_pipeline(cfg, db)
    assert first["errors"] == 1
    episode = db.list_episodes()[0]
    assert episode["status"] == "error"
    assert episode["attempts"] == 1
    assert episode["last_error"]

    cfg.transcode.ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
    second = run_pipeline(cfg, db)
    assert second["packaged"] == 1
    assert second["delivered"] == 1
    episode = db.list_episodes()[0]
    assert episode["status"] == "delivered"
    assert episode["attempts"] == 0
    assert episode["last_error"] is None
