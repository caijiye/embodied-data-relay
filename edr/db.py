from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE NOT NULL,
  path TEXT NOT NULL,
  robot_id TEXT,
  site TEXT,
  task TEXT,
  started_at TEXT,
  completed_at TEXT,
  status TEXT NOT NULL DEFAULT 'discovered',
  raw_bytes INTEGER NOT NULL DEFAULT 0,
  compact_bytes INTEGER NOT NULL DEFAULT 0,
  delivered_bytes INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS episodes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  path TEXT NOT NULL,
  camera_count INTEGER NOT NULL DEFAULT 0,
  frame_count INTEGER NOT NULL DEFAULT 0,
  raw_bytes INTEGER NOT NULL DEFAULT 0,
  compact_bytes INTEGER NOT NULL DEFAULT 0,
  quality_score REAL,
  quality_status TEXT,
  quality_json TEXT,
  manifest_json TEXT,
  tier TEXT NOT NULL DEFAULT 'incoming',
  package_path TEXT,
  status TEXT NOT NULL DEFAULT 'discovered',
  attempts INTEGER NOT NULL DEFAULT 0,
  last_error TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(session_id, name),
  FOREIGN KEY(session_id) REFERENCES sessions(id)
);

CREATE TABLE IF NOT EXISTS deliveries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  episode_id INTEGER NOT NULL,
  target TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  bytes INTEGER NOT NULL DEFAULT 0,
  attempts INTEGER NOT NULL DEFAULT 0,
  error TEXT,
  started_at TEXT,
  finished_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(episode_id) REFERENCES episodes(id)
);

CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  level TEXT NOT NULL DEFAULT 'info',
  component TEXT NOT NULL,
  message TEXT NOT NULL,
  meta_json TEXT
);

CREATE TABLE IF NOT EXISTS benchmarks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  name TEXT NOT NULL,
  config_json TEXT,
  results_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_episodes_session ON episodes(session_id);
CREATE INDEX IF NOT EXISTS idx_episodes_status ON episodes(status);
CREATE INDEX IF NOT EXISTS idx_deliveries_episode ON deliveries(episode_id);
CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts);
"""


class Database:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.init_schema()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def init_schema(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA)
            columns = {row[1] for row in conn.execute("PRAGMA table_info(episodes)").fetchall()}
            if "manifest_json" not in columns:
                conn.execute("ALTER TABLE episodes ADD COLUMN manifest_json TEXT")
            if "attempts" not in columns:
                conn.execute("ALTER TABLE episodes ADD COLUMN attempts INTEGER NOT NULL DEFAULT 0")
            if "last_error" not in columns:
                conn.execute("ALTER TABLE episodes ADD COLUMN last_error TEXT")

    # ---- sessions ----

    def upsert_session(
        self,
        *,
        name: str,
        path: str,
        robot_id: str | None = None,
        site: str | None = None,
        task: str | None = None,
        started_at: str | None = None,
        completed_at: str | None = None,
        status: str = "discovered",
        raw_bytes: int = 0,
    ) -> int:
        now = utcnow()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO sessions (name, path, robot_id, site, task, started_at, completed_at,
                                      status, raw_bytes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                  path=excluded.path,
                  robot_id=COALESCE(excluded.robot_id, sessions.robot_id),
                  site=COALESCE(excluded.site, sessions.site),
                  task=COALESCE(excluded.task, sessions.task),
                  started_at=COALESCE(excluded.started_at, sessions.started_at),
                  completed_at=COALESCE(excluded.completed_at, sessions.completed_at),
                  status=CASE WHEN sessions.status='completed' THEN sessions.status ELSE excluded.status END,
                  raw_bytes=excluded.raw_bytes,
                  updated_at=excluded.updated_at
                """,
                (name, path, robot_id, site, task, started_at, completed_at, status, raw_bytes, now, now),
            )
            row = conn.execute("SELECT id FROM sessions WHERE name = ?", (name,)).fetchone()
            return int(row["id"])

    def set_session_status(self, session_id: int, status: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE sessions SET status=?, updated_at=? WHERE id=?",
                (status, utcnow(), session_id),
            )

    def update_session_bytes(self, session_id: int) -> None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT COALESCE(SUM(raw_bytes),0) AS raw, COALESCE(SUM(compact_bytes),0) AS compact "
                "FROM episodes WHERE session_id=?",
                (session_id,),
            ).fetchone()
            conn.execute(
                "UPDATE sessions SET raw_bytes=?, compact_bytes=?, updated_at=? WHERE id=?",
                (int(row["raw"]), int(row["compact"]), utcnow(), session_id),
            )

    def refresh_session_rollups(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE sessions SET
                  raw_bytes = COALESCE((SELECT SUM(e.raw_bytes) FROM episodes e WHERE e.session_id=sessions.id), 0),
                  compact_bytes = COALESCE((SELECT SUM(e.compact_bytes) FROM episodes e WHERE e.session_id=sessions.id), 0),
                  delivered_bytes = COALESCE((
                    SELECT SUM(d.bytes) FROM deliveries d
                    JOIN episodes e ON e.id = d.episode_id
                    WHERE e.session_id = sessions.id AND d.status='delivered'
                  ), 0),
                  status = CASE
                    WHEN NOT EXISTS (
                      SELECT 1 FROM episodes e
                      WHERE e.session_id = sessions.id
                        AND e.status NOT IN ('delivered','quarantined','incomplete')
                    ) THEN 'completed'
                    ELSE sessions.status
                  END,
                  updated_at = ?
                """,
                (utcnow(),),
            )

    def list_sessions(self, limit: int = 100) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT s.*,
                       COUNT(e.id) AS episode_count,
                       COALESCE(SUM(e.raw_bytes),0) AS episode_raw_bytes,
                       COALESCE(SUM(e.compact_bytes),0) AS episode_compact_bytes,
                       COALESCE(AVG(e.quality_score),0) AS avg_quality
                FROM sessions s
                LEFT JOIN episodes e ON e.session_id = s.id
                GROUP BY s.id
                ORDER BY s.id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_session(self, session_id: int) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
            if not row:
                return None
            session = dict(row)
            episodes = conn.execute(
                "SELECT * FROM episodes WHERE session_id=? ORDER BY id", (session_id,)
            ).fetchall()
            session["episodes"] = [dict(e) for e in episodes]
            return session

    # ---- episodes ----

    def upsert_episode(
        self,
        *,
        session_id: int,
        name: str,
        path: str,
        camera_count: int = 0,
        frame_count: int = 0,
        raw_bytes: int = 0,
        status: str = "discovered",
    ) -> int:
        now = utcnow()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO episodes (session_id, name, path, camera_count, frame_count, raw_bytes,
                                     status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id, name) DO UPDATE SET
                  path=excluded.path,
                  camera_count=excluded.camera_count,
                  frame_count=excluded.frame_count,
                  raw_bytes=excluded.raw_bytes,
                  updated_at=excluded.updated_at
                """,
                (session_id, name, path, camera_count, frame_count, raw_bytes, status, now, now),
            )
            row = conn.execute(
                "SELECT id FROM episodes WHERE session_id=? AND name=?", (session_id, name)
            ).fetchone()
            return int(row["id"])

    def update_episode_quality(self, episode_id: int, report: dict[str, Any]) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE episodes SET quality_score=?, quality_status=?, quality_json=?, status=?, updated_at=? "
                "WHERE id=?",
                (
                    report.get("score"),
                    report.get("status"),
                    json.dumps(report, ensure_ascii=False),
                    "quality_" + str(report.get("status", "review")),
                    utcnow(),
                    episode_id,
                ),
            )

    def update_episode_package(
        self, episode_id: int, package_path: str, compact_bytes: int, manifest: dict[str, Any]
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE episodes SET package_path=?, compact_bytes=?, tier='hot', status='packaged', "
                "manifest_json=?, attempts=0, last_error=NULL, updated_at=? WHERE id=?",
                (
                    package_path,
                    compact_bytes,
                    json.dumps(manifest, ensure_ascii=False),
                    utcnow(),
                    episode_id,
                ),
            )

    def set_episode_tier(self, episode_id: int, tier: str, package_path: str | None = None) -> None:
        with self.connect() as conn:
            if package_path is None:
                conn.execute(
                    "UPDATE episodes SET tier=?, updated_at=? WHERE id=?",
                    (tier, utcnow(), episode_id),
                )
            else:
                conn.execute(
                    "UPDATE episodes SET tier=?, package_path=?, updated_at=? WHERE id=?",
                    (tier, package_path, utcnow(), episode_id),
                )

    def set_episode_status(self, episode_id: int, status: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE episodes SET status=?, updated_at=? WHERE id=?",
                (status, utcnow(), episode_id),
            )

    def list_episodes(
        self, status: str | None = None, session_id: int | None = None, limit: int = 1000
    ) -> list[dict[str, Any]]:
        sql = "SELECT e.*, s.name AS session_name FROM episodes e JOIN sessions s ON s.id=e.session_id"
        clauses: list[str] = []
        params: list[Any] = []
        if status:
            clauses.append("e.status=?")
            params.append(status)
        if session_id is not None:
            clauses.append("e.session_id=?")
            params.append(session_id)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += (
            " ORDER BY CASE e.quality_status WHEN 'pass' THEN 0 WHEN 'review' THEN 1 ELSE 2 END, "
            "e.id DESC LIMIT ?"
        )
        params.append(limit)
        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]

    def list_episodes_for_processing(self, max_attempts: int, limit: int = 1000) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT e.*, s.name AS session_name
                FROM episodes e JOIN sessions s ON s.id = e.session_id
                WHERE e.status IN ('discovered','quality_pass','quality_review','error')
                  AND e.attempts < ?
                ORDER BY e.id ASC
                LIMIT ?
                """,
                (max_attempts, limit),
            ).fetchall()
            return [dict(r) for r in rows]

    def requeue_episodes(self, statuses: tuple[str, ...] = ("error", "failed")) -> int:
        if not statuses:
            return 0
        placeholders = ",".join("?" for _ in statuses)
        with self.connect() as conn:
            cur = conn.execute(
                f"UPDATE episodes SET status='discovered', attempts=0, last_error=NULL, updated_at=? "
                f"WHERE status IN ({placeholders})",
                (utcnow(), *statuses),
            )
            return int(cur.rowcount or 0)

    def mark_episode_error(self, episode_id: int, error: str, max_attempts: int) -> tuple[str, int]:
        with self.connect() as conn:
            row = conn.execute("SELECT attempts FROM episodes WHERE id=?", (episode_id,)).fetchone()
            attempts = int(row["attempts"] or 0) + 1
            status = "failed" if attempts >= max_attempts else "error"
            conn.execute(
                "UPDATE episodes SET attempts=?, last_error=?, status=?, updated_at=? WHERE id=?",
                (attempts, error, status, utcnow(), episode_id),
            )
            return status, attempts

    def get_episode(self, episode_id: int) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT e.*, s.name AS session_name FROM episodes e JOIN sessions s ON s.id=e.session_id "
                "WHERE e.id=?",
                (episode_id,),
            ).fetchone()
            return dict(row) if row else None

    # ---- deliveries ----

    def create_delivery(self, episode_id: int, target: str) -> int:
        now = utcnow()
        with self.connect() as conn:
            cur = conn.execute(
                "INSERT INTO deliveries (episode_id, target, status, created_at, updated_at) "
                "VALUES (?, ?, 'pending', ?, ?)",
                (episode_id, target, now, now),
            )
            return int(cur.lastrowid)

    def update_delivery(
        self,
        delivery_id: int,
        *,
        status: str,
        bytes_uploaded: int = 0,
        attempts: int = 0,
        error: str | None = None,
        started_at: str | None = None,
        finished_at: str | None = None,
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE deliveries SET status=?, bytes=?, attempts=?, error=?,
                  started_at=COALESCE(?, started_at), finished_at=COALESCE(?, finished_at), updated_at=?
                WHERE id=?
                """,
                (status, bytes_uploaded, attempts, error, started_at, finished_at, utcnow(), delivery_id),
            )

    def latest_delivery(self, episode_id: int) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM deliveries WHERE episode_id=? ORDER BY id DESC LIMIT 1",
                (episode_id,),
            ).fetchone()
            return dict(row) if row else None

    # ---- events ----

    def add_event(self, level: str, component: str, message: str, meta: dict[str, Any] | None = None) -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO events (ts, level, component, message, meta_json) VALUES (?, ?, ?, ?, ?)",
                (utcnow(), level, component, message, json.dumps(meta or {}, ensure_ascii=False)),
            )

    def recent_events(self, limit: int = 50) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    # ---- stats ----

    def stats(self) -> dict[str, Any]:
        with self.connect() as conn:
            sessions = conn.execute(
                "SELECT COUNT(*) AS n, COALESCE(SUM(raw_bytes),0) AS raw, "
                "COALESCE(SUM(compact_bytes),0) AS compact, COALESCE(SUM(delivered_bytes),0) AS delivered "
                "FROM sessions"
            ).fetchone()
            episodes = conn.execute(
                "SELECT COUNT(*) AS n, COALESCE(SUM(raw_bytes),0) AS raw, "
                "COALESCE(SUM(compact_bytes),0) AS compact FROM episodes"
            ).fetchone()
            quality = {
                row["quality_status"] or "unknown": row["n"]
                for row in conn.execute(
                    "SELECT quality_status, COUNT(*) AS n FROM episodes GROUP BY quality_status"
                ).fetchall()
            }
            tiers = {
                row["tier"] or "unknown": row["n"]
                for row in conn.execute(
                    "SELECT tier, COUNT(*) AS n FROM episodes GROUP BY tier"
                ).fetchall()
            }
            statuses = {
                row["status"] or "unknown": row["n"]
                for row in conn.execute(
                    "SELECT status, COUNT(*) AS n FROM episodes GROUP BY status"
                ).fetchall()
            }
            delivered = conn.execute(
                "SELECT COALESCE(SUM(bytes),0) AS bytes FROM deliveries WHERE status='delivered'"
            ).fetchone()
            latency = conn.execute(
                """
                SELECT AVG((julianday(d.finished_at) - julianday(s.completed_at)) * 24.0) AS hours
                FROM deliveries d
                JOIN episodes e ON e.id = d.episode_id
                JOIN sessions s ON s.id = e.session_id
                WHERE d.status='delivered' AND d.finished_at IS NOT NULL AND s.completed_at IS NOT NULL
                """
            ).fetchone()
            raw = int(episodes["raw"] or 0)
            compact = int(episodes["compact"] or 0)
            reduction = (1 - compact / raw) if raw > 0 and compact > 0 else 0.0
            return {
                "sessions": int(sessions["n"] or 0),
                "episodes": int(episodes["n"] or 0),
                "raw_bytes": raw,
                "compact_bytes": compact,
                "delivered_bytes": int(delivered["bytes"] or 0),
                "reduction_ratio": round(reduction, 4),
                "quality": quality,
                "tiers": tiers,
                "statuses": statuses,
                "avg_delivery_hours": round(float(latency["hours"] or 0), 3),
            }

    # ---- benchmarks ----

    def add_benchmark(self, name: str, config: dict[str, Any], results: dict[str, Any]) -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO benchmarks (ts, name, config_json, results_json) VALUES (?, ?, ?, ?)",
                (utcnow(), name, json.dumps(config, ensure_ascii=False), json.dumps(results, ensure_ascii=False)),
            )

    def latest_benchmark(self) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM benchmarks ORDER BY id DESC LIMIT 1").fetchone()
            if not row:
                return None
            data = dict(row)
            data["config"] = json.loads(data.pop("config_json") or "{}")
            data["results"] = json.loads(data.pop("results_json") or "{}")
            return data
