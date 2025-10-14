import os
from pathlib import Path

import toml

from omnivocal.config import CONFIG_DIR, CONFIG_PATH, OmnivocalConfig, ensure_config, load_config, set_config_value


def test_ensure_config_creates_file(tmp_path, monkeypatch):
    monkeypatch.setenv("OMNIVOCAL_CONFIG_DIR", str(tmp_path))
    path = ensure_config()
    assert path.exists()
    data = toml.load(path)
    assert data["chutes"]["endpoint"] == "https://chutes-whisper-large-v3.chutes.ai/transcribe"


def test_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("OMNIVOCAL_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv("OMNIVOCAL_CHUTES_TIMEOUT_SECONDS", "60")
    config = load_config()
    assert config.chutes.timeout_seconds == 60


def test_set_config_value_updates(monkeypatch, tmp_path):
    monkeypatch.setenv("OMNIVOCAL_CONFIG_DIR", str(tmp_path))
    config = load_config()
    set_config_value(config, "chutes.max_retries", "5")
    assert config.chutes.max_retries == 5
