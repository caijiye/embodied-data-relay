"""Import a LeRobotDataset (v3 file layout) episode into the EDR input layout.

This is a pilot/benchmark adapter, not part of the core runtime. It requires
pyarrow: install with `uv pip install -e ".[pilot]"`.

Example:
  python scripts/import_lerobot.py \
    --dataset data/public/pusht \
    --out data/real_pilot/incoming \
    --episodes 2 --frames 100
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as pq


def _parquet_rows(path: Path) -> list[dict]:
    return pq.read_table(path).to_pylist()


def _resolve_template(template: str, values: dict) -> Path:
    return Path(template.format(**values))


def _extract_frames(video: Path, start: float, end: float, out_dir: Path, frames: int) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    duration = max(end - start, 0.0)
    if duration <= 0:
        return 0
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video),
        "-ss",
        f"{start:.3f}",
        "-t",
        f"{duration:.3f}",
        "-fps_mode",
        "passthrough",
        "-frames:v",
        str(frames),
        str(out_dir / "%06d.png"),
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return len(list(out_dir.glob("*.png")))


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert LeRobotDataset episodes to EDR input sessions")
    parser.add_argument("--dataset", default="data/public/pusht")
    parser.add_argument("--out", default="data/real_pilot/incoming")
    parser.add_argument("--session", default="session_pusht_001")
    parser.add_argument("--episodes", type=int, default=2)
    parser.add_argument("--frames", type=int, default=100)
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()

    dataset = Path(args.dataset).resolve()
    info = json.loads((dataset / "meta" / "info.json").read_text(encoding="utf-8"))
    episode_files = sorted((dataset / "meta" / "episodes").rglob("*.parquet"))
    if not episode_files:
        raise SystemExit("no meta/episodes parquet found")
    episodes: list[dict] = []
    for p in episode_files:
        episodes.extend(_parquet_rows(p))
    episodes.sort(key=lambda e: e["episode_index"])
    episodes = episodes[: args.episodes]

    data_files = sorted((dataset / "data").rglob("*.parquet"))
    if not data_files:
        raise SystemExit("no data parquet found")
    rows_by_episode: dict[int, list[dict]] = {}
    for p in data_files:
        for row in _parquet_rows(p):
            rows_by_episode.setdefault(int(row["episode_index"]), []).append(row)
    for rows in rows_by_episode.values():
        rows.sort(key=lambda r: r["frame_index"])

    session_dir = Path(args.out).resolve() / args.session
    if args.clean and session_dir.exists():
        shutil.rmtree(session_dir)
    session_dir.mkdir(parents=True, exist_ok=True)

    session_meta = {
        "session": args.session,
        "robot_type": info.get("robot_type", "unknown"),
        "site": "public-dataset",
        "task": episodes[0]["tasks"][0] if episodes and episodes[0].get("tasks") else None,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "source": "lerobot/pusht",
        "source_url": "https://huggingface.co/datasets/lerobot/pusht",
        "license": "MIT",
        "fps": info.get("fps", 10),
        "cameras": ["front"],
    }
    (session_dir / "meta.json").write_text(json.dumps(session_meta, ensure_ascii=False, indent=2), encoding="utf-8")

    total_frames = 0
    for meta in episodes:
        ep_index = int(meta["episode_index"])
        ep_name = f"episode_{ep_index:04d}"
        ep_dir = session_dir / ep_name
        ep_dir.mkdir(parents=True, exist_ok=True)

        video_key = "observation.image"
        video_rel = _resolve_template(
            info["video_path"],
            {
                "video_key": video_key,
                "chunk_index": int(meta[f"videos/{video_key}/chunk_index"]),
                "file_index": int(meta[f"videos/{video_key}/file_index"]),
            },
        )
        video_path = dataset / video_rel
        frames_dir = ep_dir / f"camera_front" / "frames"
        frame_count = _extract_frames(
            video_path,
            float(meta[f"videos/{video_key}/from_timestamp"]),
            float(meta[f"videos/{video_key}/to_timestamp"]),
            frames_dir,
            args.frames,
        )
        if frame_count == 0:
            raise SystemExit(f"no frames extracted for episode {ep_index}")

        rows = rows_by_episode.get(ep_index, [])[:frame_count]
        with (ep_dir / "state.jsonl").open("w", encoding="utf-8") as fh:
            for row in rows:
                payload = {
                    "t": row.get("timestamp"),
                    "frame_index": row.get("frame_index"),
                    "observation.state": row.get("observation.state"),
                    "action": row.get("action"),
                    "next.reward": row.get("next.reward"),
                    "next.done": row.get("next.done"),
                    "next.success": row.get("next.success"),
                }
                fh.write(json.dumps(payload, ensure_ascii=False) + "\n")

        episode_meta = {
            "episode": ep_name,
            "task": meta["tasks"][0] if meta.get("tasks") else None,
            "success": bool(rows[-1].get("next.success")) if rows else False,
            "fps": info.get("fps", 10),
            "cameras": ["front"],
            "source_video": str(video_rel),
            "source_from_timestamp": meta[f"videos/{video_key}/from_timestamp"],
            "source_to_timestamp": meta[f"videos/{video_key}/to_timestamp"],
            "license": "MIT",
        }
        (ep_dir / "meta.json").write_text(json.dumps(episode_meta, ensure_ascii=False, indent=2), encoding="utf-8")
        total_frames += frame_count
        print(f"{ep_name}: {frame_count} frames, {len(rows)} state rows")

    (session_dir / "_COMPLETE").write_text(datetime.now(timezone.utc).isoformat() + "\n", encoding="utf-8")
    print(json.dumps({"session": args.session, "episodes": len(episodes), "frames": total_frames, "output": str(session_dir)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
