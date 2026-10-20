from __future__ import annotations

from edr.config import QualityConfig
from edr.quality import analyze_episode
from tests.conftest import make_episode


def test_sharp_passes(tmp_path):
    episode = make_episode(tmp_path, "episode_sharp", "sharp")
    report = analyze_episode(episode, QualityConfig())
    assert report["status"] == "pass"
    assert report["score"] >= 70
    assert not report["reasons"]


def test_blur_is_flagged(tmp_path):
    episode = make_episode(tmp_path, "episode_blur", "blur")
    report = analyze_episode(episode, QualityConfig())
    assert report["status"] in {"review", "quarantine"}
    assert any("blur" in reason for reason in report["reasons"])


def test_dark_is_quarantined(tmp_path):
    episode = make_episode(tmp_path, "episode_dark", "dark")
    report = analyze_episode(episode, QualityConfig())
    assert report["status"] == "quarantine"


def test_black_is_quarantined(tmp_path):
    episode = make_episode(tmp_path, "episode_black", "black")
    report = analyze_episode(episode, QualityConfig())
    assert report["status"] == "quarantine"


def test_duplicate_is_quarantined(tmp_path):
    episode = make_episode(tmp_path, "episode_duplicate", "duplicate")
    report = analyze_episode(episode, QualityConfig())
    assert report["status"] == "quarantine"
    assert any("duplicate" in reason for reason in report["reasons"])


def test_bright_is_flagged(tmp_path):
    episode = make_episode(tmp_path, "episode_bright", "bright")
    report = analyze_episode(episode, QualityConfig())
    assert report["status"] in {"review", "quarantine"}
    assert any("bright" in reason for reason in report["reasons"])
