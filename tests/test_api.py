from __future__ import annotations

from fastapi.testclient import TestClient

from edr.api import create_app
from edr.config import Config, PathsConfig
from edr.db import Database


def test_health_and_stats(tmp_path):
    cfg = Config(
        base_dir=tmp_path,
        paths=PathsConfig(
            incoming=tmp_path / "incoming",
            hot=tmp_path / "hot",
            cold=tmp_path / "cold",
            quarantine=tmp_path / "quarantine",
            db=tmp_path / "edr.db",
            logs=tmp_path / "logs",
        ),
    )
    cfg.ensure_dirs()
    db = Database(cfg.paths.db)
    client = TestClient(create_app(cfg, db))

    assert client.get("/healthz").json()["status"] == "ok"
    stats = client.get("/api/stats").json()
    assert stats["episodes"] == 0
    dashboard = client.get("/api/dashboard").json()
    assert "stats" in dashboard and "telemetry" in dashboard
    page = client.get("/")
    assert page.status_code == 200
    assert "具身数据驿" in page.text
