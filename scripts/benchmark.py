"""Benchmark: raw archive/upload baseline vs the Embodied Data Relay pipeline.

The benchmark writes only under data/benchmark/ and never touches demo data.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from edr.config import PathsConfig, load_config
from edr.db import Database
from edr.pipeline import run_pipeline


def _dir_bytes(path: Path) -> int:
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def _remove(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def _modeled_upload_seconds(nbytes: int, uplink_mbps: float) -> float:
    if uplink_mbps <= 0:
        return 0.0
    return (nbytes * 8) / (uplink_mbps * 1_000_000)


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark baseline vs EDR pipeline")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--sessions", type=int, default=2)
    parser.add_argument("--episodes", type=int, default=7)
    parser.add_argument("--cameras", type=int, default=2)
    parser.add_argument("--frames", type=int, default=30)
    parser.add_argument("--width", type=int, default=320)
    parser.add_argument("--height", type=int, default=240)
    parser.add_argument("--noise", type=float, default=4.0)
    parser.add_argument("--uplink-mbps", type=float, default=100.0)
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()

    base_cfg = load_config(args.config)
    bench_root = base_cfg.base_dir / "data" / "benchmark"
    incoming = bench_root / "incoming"
    baseline_dir = bench_root / "baseline_archive"
    baseline_delivered = bench_root / "baseline_delivered"
    bench_db_path = bench_root / "benchmark.db"

    if args.clean:
        _remove(bench_root)
    bench_root.mkdir(parents=True, exist_ok=True)
    _remove(baseline_dir)
    _remove(baseline_delivered)
    for name in ("hot", "cold", "delivered", "quarantine", "logs"):
        _remove(bench_root / name)
    for suffix in ("", "-wal", "-shm"):
        p = Path(str(bench_db_path) + suffix)
        if p.exists():
            p.unlink()

    if not incoming.exists() or not any(incoming.glob("*/_COMPLETE")):
        print("generating synthetic dataset...", flush=True)
        subprocess.run(
            [
                sys.executable,
                str(base_cfg.base_dir / "scripts" / "synth_recorder.py"),
                "--out",
                str(incoming),
                "--sessions",
                str(args.sessions),
                "--episodes",
                str(args.episodes),
                "--cameras",
                str(args.cameras),
                "--frames",
                str(args.frames),
                "--width",
                str(args.width),
                "--height",
                str(args.height),
                "--noise",
                str(args.noise),
                "--clean",
            ],
            check=True,
            cwd=str(base_cfg.base_dir),
        )

    raw_bytes = _dir_bytes(incoming)

    # Baseline: keep everything, upload everything.
    t0 = time.perf_counter()
    shutil.copytree(incoming, baseline_dir)
    baseline_seconds = time.perf_counter() - t0
    t0 = time.perf_counter()
    shutil.copytree(incoming, baseline_delivered)
    baseline_delivery_seconds = time.perf_counter() - t0
    baseline_upload_modeled = _modeled_upload_seconds(raw_bytes, args.uplink_mbps)
    baseline_total = baseline_seconds + baseline_upload_modeled

    cfg = replace(
        base_cfg,
        paths=PathsConfig(
            incoming=incoming,
            hot=bench_root / "hot",
            cold=bench_root / "cold",
            quarantine=bench_root / "quarantine",
            db=bench_db_path,
            logs=bench_root / "logs",
        ),
    )
    cfg.delivery.enabled = True
    cfg.delivery.target = "local"
    cfg.delivery.local_dir = bench_root / "delivered"
    cfg.tiering.hot_sessions = 1
    cfg.tiering.auto_tier = True
    cfg.ensure_dirs()
    db = Database(cfg.paths.db)

    t0 = time.perf_counter()
    summary = run_pipeline(cfg, db, limit=10000)
    pipeline_seconds = time.perf_counter() - t0
    stats = db.stats()

    with db.connect() as conn:
        usable_raw = int(
            conn.execute(
                "SELECT COALESCE(SUM(raw_bytes),0) AS n FROM episodes WHERE status IN ('packaged','delivered')"
            ).fetchone()["n"]
        )

    compact = int(stats["compact_bytes"])
    delivered = int(stats["delivered_bytes"])
    pipeline_upload_modeled = _modeled_upload_seconds(delivered, args.uplink_mbps)
    pipeline_total = pipeline_seconds + pipeline_upload_modeled

    quality_drop = 1 - usable_raw / raw_bytes if raw_bytes else 0.0
    codec_reduction = 1 - compact / usable_raw if usable_raw else 0.0
    total_reduction = 1 - compact / raw_bytes if raw_bytes else 0.0

    results = {
        "dataset": {
            "sessions": args.sessions,
            "episodes": args.sessions * args.episodes,
            "cameras": args.cameras,
            "frames": args.frames,
            "resolution": f"{args.width}x{args.height}",
            "raw_bytes": raw_bytes,
            "source": "synthetic multi-camera sessions with injected blur/dark/duplicate/black/bright defects",
        },
        "baseline": {
            "bytes": raw_bytes,
            "copy_seconds": round(baseline_seconds, 3),
            "local_delivery_seconds": round(baseline_delivery_seconds, 3),
            "modeled_upload_seconds": round(baseline_upload_modeled, 3),
            "total_seconds": round(baseline_total, 3),
            "data_to_training_hours": round(baseline_total / 3600, 4),
        },
        "pipeline": {
            "raw_bytes": raw_bytes,
            "usable_raw_bytes": usable_raw,
            "compact_bytes": compact,
            "delivered_bytes": delivered,
            "quality_drop_ratio": round(quality_drop, 4),
            "codec_reduction_ratio": round(codec_reduction, 4),
            "reduction_ratio": round(total_reduction, 4),
            "seconds": round(pipeline_seconds, 3),
            "modeled_upload_seconds": round(pipeline_upload_modeled, 3),
            "total_seconds": round(pipeline_total, 3),
            "data_to_training_hours": round(pipeline_total / 3600, 4),
        },
        "speedup": round(baseline_total / pipeline_total, 2) if pipeline_total > 0 else 0.0,
        "uplink_mbps": args.uplink_mbps,
        "quality": stats["quality"],
        "tiers": stats["tiers"],
        "statuses": stats["statuses"],
        "pipeline_summary": summary,
        "notes": [
            "Synthetic raw frames are stored as PNG; codec reduction is an upper bound and will be lower on real sensor data.",
            "Upload time is modeled at the configured uplink; local copy time is measured separately.",
            "Quality drop is the share of raw bytes excluded by the edge quality gate (quarantine).",
        ],
    }

    out_path = bench_root / "benchmark_results.json"
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    main_db = Database(base_cfg.paths.db)
    main_db.add_benchmark(
        "baseline_vs_pipeline",
        {
            "sessions": args.sessions,
            "episodes": args.episodes,
            "cameras": args.cameras,
            "frames": args.frames,
            "uplink_mbps": args.uplink_mbps,
        },
        results,
    )

    print(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"\nresults written to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
