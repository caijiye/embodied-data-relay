from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class PathsConfig:
    incoming: Path
    hot: Path
    cold: Path
    quarantine: Path
    db: Path
    logs: Path


@dataclass
class ScannerConfig:
    settle_seconds: int = 2
    require_complete_marker: bool = True


@dataclass
class QualityConfig:
    sample_frames: int = 12
    blur_threshold: float = 60.0
    dark_threshold: float = 25.0
    bright_threshold: float = 230.0
    black_frame_threshold: float = 0.3
    duplicate_threshold: float = 0.5
    review_score: float = 70.0
    quarantine_score: float = 50.0


@dataclass
class TranscodeConfig:
    ffmpeg: str = "ffmpeg"
    fps: int = 30
    crf: int = 23
    preset: str = "veryfast"
    video_codec: str = "libx264"


@dataclass
class TieringConfig:
    hot_sessions: int = 3
    auto_tier: bool = True


@dataclass
class DeliveryConfig:
    enabled: bool = True
    target: str = "local"
    local_dir: Path = Path("data/delivered")
    endpoint: str = "http://127.0.0.1:9000"
    access_key: str = "minioadmin"
    secret_key: str = "minioadmin"
    bucket: str = "edr-delivery"
    region: str = "us-east-1"
    prefix: str = "embodied"
    max_attempts: int = 3
    bandwidth_limit_mbps: int = 0


@dataclass
class PipelineConfig:
    max_attempts: int = 3
    min_free_gb: float = 2.0


@dataclass
class ServerConfig:
    host: str = "127.0.0.1"
    port: int = 8080


@dataclass
class Config:
    base_dir: Path
    paths: PathsConfig
    scanner: ScannerConfig = field(default_factory=ScannerConfig)
    quality: QualityConfig = field(default_factory=QualityConfig)
    transcode: TranscodeConfig = field(default_factory=TranscodeConfig)
    tiering: TieringConfig = field(default_factory=TieringConfig)
    delivery: DeliveryConfig = field(default_factory=DeliveryConfig)
    pipeline: PipelineConfig = field(default_factory=PipelineConfig)
    server: ServerConfig = field(default_factory=ServerConfig)

    def ensure_dirs(self) -> None:
        for p in (
            self.paths.incoming,
            self.paths.hot,
            self.paths.cold,
            self.paths.quarantine,
            self.paths.logs,
            self.delivery.local_dir,
        ):
            p.mkdir(parents=True, exist_ok=True)
        self.paths.db.parent.mkdir(parents=True, exist_ok=True)


def _resolve(base: Path, value: str | Path) -> Path:
    p = Path(value)
    return p if p.is_absolute() else (base / p).resolve()


def load_config(path: str | Path = "config.yaml") -> Config:
    cfg_path = Path(path).resolve()
    base = cfg_path.parent
    raw: dict[str, Any] = {}
    if cfg_path.exists():
        raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}

    paths_raw = raw.get("paths", {})
    paths = PathsConfig(
        incoming=_resolve(base, paths_raw.get("incoming", "data/incoming")),
        hot=_resolve(base, paths_raw.get("hot", "data/hot")),
        cold=_resolve(base, paths_raw.get("cold", "data/cold")),
        quarantine=_resolve(base, paths_raw.get("quarantine", "data/quarantine")),
        db=_resolve(base, paths_raw.get("db", "data/edr.db")),
        logs=_resolve(base, paths_raw.get("logs", "data/logs")),
    )

    scanner = ScannerConfig(**raw.get("scanner", {}))
    quality = QualityConfig(**raw.get("quality", {}))
    transcode = TranscodeConfig(**raw.get("transcode", {}))
    tiering = TieringConfig(**raw.get("tiering", {}))

    delivery_raw = dict(raw.get("delivery", {}))
    delivery_raw["endpoint"] = os.getenv(
        "EDR_S3_ENDPOINT", delivery_raw.get("endpoint", "http://127.0.0.1:9000")
    )
    delivery_raw["access_key"] = os.getenv(
        "EDR_S3_ACCESS_KEY", delivery_raw.get("access_key", "minioadmin")
    )
    delivery_raw["secret_key"] = os.getenv(
        "EDR_S3_SECRET_KEY", delivery_raw.get("secret_key", "minioadmin")
    )
    delivery_raw["bucket"] = os.getenv("EDR_S3_BUCKET", delivery_raw.get("bucket", "edr-delivery"))
    if "local_dir" in delivery_raw:
        delivery_raw["local_dir"] = _resolve(base, delivery_raw["local_dir"])
    else:
        delivery_raw["local_dir"] = _resolve(base, "data/delivered")
    delivery = DeliveryConfig(**delivery_raw)
    pipeline = PipelineConfig(**raw.get("pipeline", {}))
    server = ServerConfig(**raw.get("server", {}))
    cfg = Config(
        base_dir=base,
        paths=paths,
        scanner=scanner,
        quality=quality,
        transcode=transcode,
        tiering=tiering,
        delivery=delivery,
        pipeline=pipeline,
        server=server,
    )
    cfg.ensure_dirs()
    return cfg
