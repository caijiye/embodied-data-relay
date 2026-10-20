from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psutil
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import Config
from .db import Database

WEB_DIR = Path(__file__).parent / "web"


def human_bytes(value: float | int) -> str:
    value = float(value or 0)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(value) < 1024 or unit == "TB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{value:.1f} TB"


def create_app(cfg: Config, db: Database) -> FastAPI:
    app = FastAPI(title="Embodied Data Relay", version="0.1.0")
    app.state.cfg = cfg
    app.state.db = db
    app.state.device_telemetry = {}

    templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))
    templates.env.filters["human_bytes"] = human_bytes
    app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")

    def telemetry() -> dict[str, Any]:
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage(str(cfg.paths.db.parent))
        return {
            "host": {
                "cpu_percent": psutil.cpu_percent(interval=None),
                "memory_percent": mem.percent,
                "memory_used": mem.used,
                "memory_total": mem.total,
                "disk_percent": disk.percent,
                "disk_used": disk.used,
                "disk_total": disk.total,
            },
            "device": app.state.device_telemetry,
            "ts": datetime.now(timezone.utc).isoformat(),
        }

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request):
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "stats": db.stats(),
                "sessions": db.list_sessions(limit=20),
                "events": db.recent_events(limit=20),
                "benchmark": db.latest_benchmark(),
                "cfg": cfg,
            },
        )

    @app.get("/api/dashboard")
    def dashboard() -> dict[str, Any]:
        return {
            "stats": db.stats(),
            "sessions": db.list_sessions(limit=20),
            "events": db.recent_events(limit=20),
            "telemetry": telemetry(),
            "benchmark": db.latest_benchmark(),
        }

    @app.get("/api/stats")
    def stats() -> dict[str, Any]:
        return db.stats()

    @app.get("/api/sessions")
    def sessions(limit: int = 50) -> list[dict[str, Any]]:
        return db.list_sessions(limit=limit)

    @app.get("/api/sessions/{session_id}")
    def session_detail(session_id: int) -> dict[str, Any]:
        session = db.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="session not found")
        return session

    @app.get("/api/episodes")
    def episodes(status: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
        return db.list_episodes(status=status, limit=limit)

    @app.get("/api/episodes/{episode_id}/file/{filename}")
    def episode_file(episode_id: int, filename: str):
        episode = db.get_episode(episode_id)
        if not episode or not episode.get("package_path"):
            raise HTTPException(status_code=404, detail="episode package not found")
        root = Path(episode["package_path"]).resolve()
        target = (root / filename).resolve()
        if root not in target.parents and target != root:
            raise HTTPException(status_code=403, detail="invalid path")
        if not target.is_file():
            raise HTTPException(status_code=404, detail="file not found")
        return FileResponse(target)

    @app.get("/api/events")
    def events(limit: int = 50) -> list[dict[str, Any]]:
        return db.recent_events(limit=limit)

    @app.get("/api/telemetry")
    def get_telemetry() -> dict[str, Any]:
        return telemetry()

    @app.post("/api/telemetry")
    async def post_telemetry(request: Request) -> JSONResponse:
        payload = await request.json()
        if not isinstance(payload, dict):
            raise HTTPException(status_code=400, detail="telemetry must be an object")
        payload["received_at"] = datetime.now(timezone.utc).isoformat()
        app.state.device_telemetry = payload
        return JSONResponse({"ok": True})

    @app.get("/api/benchmark")
    def benchmark() -> dict[str, Any] | None:
        return db.latest_benchmark()

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app
