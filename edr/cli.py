from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_config
from .db import Database
from .delivery import deliver_pending
from .pipeline import run_pipeline
from .scanner import scan_incoming
from .tiering import tier_episodes


def _print(data) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="edr", description="Embodied Data Relay CLI")
    parser.add_argument("--config", default="config.yaml", help="path to config.yaml")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("scan", help="scan incoming sessions")
    sub.add_parser("deliver", help="deliver all packaged episodes")
    sub.add_parser("tier", help="move eligible episodes to cold tier")
    sub.add_parser("report", help="print stats")
    pipeline_parser = sub.add_parser("pipeline", help="scan + quality + transcode + deliver + tier")
    pipeline_parser.add_argument("--limit", type=int, default=1000)

    serve_parser = sub.add_parser("serve", help="start dashboard")
    serve_parser.add_argument("--host", default=None)
    serve_parser.add_argument("--port", type=int, default=None)

    args = parser.parse_args(argv)
    cfg = load_config(args.config)
    db = Database(cfg.paths.db)

    if args.command == "scan":
        _print({"ready": scan_incoming(cfg, db)})
    elif args.command == "pipeline":
        _print(run_pipeline(cfg, db, limit=args.limit))
    elif args.command == "deliver":
        _print(deliver_pending(cfg, db))
    elif args.command == "tier":
        _print(tier_episodes(cfg, db))
    elif args.command == "report":
        _print(db.stats())
    elif args.command == "serve":
        import uvicorn
        from .api import create_app

        host = args.host or cfg.server.host
        port = args.port or cfg.server.port
        uvicorn.run(create_app(cfg, db), host=host, port=port)
    else:
        parser.error(f"unknown command: {args.command}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
