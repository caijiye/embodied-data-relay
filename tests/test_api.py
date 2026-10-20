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


def test_episode_file_and_path_traversal(tmp_path):
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

    session_id = db.upsert_session(name="session_test", path=str(tmp_path / "session_test"))
    episode_id = db.upsert_episode(
        session_id=session_id, name="episode_test", path=str(tmp_path / "episode_test")
    )
    package = tmp_path / "hot" / "session_test" / "episode_test"
    package.mkdir(parents=True)
    (package / "camera_front.mp4").write_bytes(b"fake-mp4")
    (tmp_path / "secret.txt").write_text("do not serve", encoding="utf-8")
    db.update_episode_package(episode_id, str(package), 8, {"files": []})

    response = client.get(f"/api/episodes/{episode_id}/file/camera_front.mp4")
    assert response.status_code == 200
    assert response.content == b"fake-mp4"

    traversal = client.get(f"/api/episodes/{episode_id}/file/..%2F..%2Fsecret.txt")
    assert traversal.status_code in {403, 404}
