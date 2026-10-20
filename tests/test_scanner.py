from __future__ import annotations

from edr.config import Config, PathsConfig, ScannerConfig
from edr.db import Database
from edr.scanner import scan_incoming


def test_incomplete_session_is_not_scanned(tmp_path):
    incoming = tmp_path / "incoming"
    (incoming / "session_partial" / "episode_0001" / "camera_front" / "frames").mkdir(parents=True)
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
        scanner=ScannerConfig(settle_seconds=999, require_complete_marker=True),
    )
    cfg.ensure_dirs()
    db = Database(cfg.paths.db)

    assert scan_incoming(cfg, db) == []
    assert db.list_sessions() == []
