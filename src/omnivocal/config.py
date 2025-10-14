"""Configuration management for Omnivocal."""

from __future__ import annotations

import os
from dataclasses import dataclass, field, asdict, fields
from pathlib import Path
from typing import Any, Dict, get_type_hints

import toml


CONFIG_DIR = Path(os.environ.get("OMNIVOCAL_CONFIG_DIR", Path.home() / ".config" / "omnivocal"))
CONFIG_PATH = CONFIG_DIR / "config.toml"
ENV_PREFIX = "OMNIVOCAL"


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        value_lower = value.strip().lower()
        if value_lower in {"1", "true", "yes", "on"}:
            return True
        if value_lower in {"0", "false", "no", "off"}:
            return False
    raise ValueError(f"Cannot coerce {value!r} to bool")


def _coerce(value: str, target: Any) -> Any:
    if isinstance(target, bool):
        return _bool(value)
    if isinstance(target, int):
        return int(value)
    if isinstance(target, float):
        return float(value)
    return value


@dataclass
class ChutesConfig:
    api_key: str = ""
    endpoint: str = "https://chutes-whisper-large-v3.chutes.ai/transcribe"
    timeout_seconds: int = 30
    max_retries: int = 3


@dataclass
class RecordingConfig:
    sample_rate: int = 16000
    channels: int = 1
    max_seconds: int = 180
    format: str = "wav"
    temp_dir: str = "/tmp/omnivocal"


@dataclass
class VadConfig:
    enabled: bool = True  # Enable VAD by default
    silence_ms_to_stop: int = 1200  # 1.2 seconds of silence to stop
    aggressiveness: int = 2  # 0-3, higher = more aggressive


@dataclass
class ClipboardConfig:
    enabled: bool = True
    command: str = "wl-copy"


@dataclass
class NotificationsConfig:
    enabled: bool = True
    command: str = "notify-send"
    title: str = "Omnivocal"


@dataclass
class UIConfig:
    show_segments: bool = False
    show_timing: bool = False
    auto_copy: bool = True


@dataclass
class OmnivocalConfig:
    chutes: ChutesConfig = field(default_factory=ChutesConfig)
    recording: RecordingConfig = field(default_factory=RecordingConfig)
    vad: VadConfig = field(default_factory=VadConfig)
    clipboard: ClipboardConfig = field(default_factory=ClipboardConfig)
    notifications: NotificationsConfig = field(default_factory=NotificationsConfig)
    ui: UIConfig = field(default_factory=UIConfig)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OmnivocalConfig":
        type_hints = get_type_hints(cls)
        kwargs: Dict[str, Any] = {}
        for field_obj in fields(cls):
            section_name = field_obj.name
            section_type = type_hints[section_name]
            section_data = data.get(section_name, {})
            kwargs[section_name] = section_type(**section_data)
        return cls(**kwargs)


def _default_config_dict() -> Dict[str, Any]:
    return OmnivocalConfig().to_dict()


def ensure_config(path: Path = CONFIG_PATH) -> Path:
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        save_config(_default_config_dict(), path)
    return path


def load_config(path: Path | None = None) -> OmnivocalConfig:
    config_path = ensure_config(path or CONFIG_PATH)
    data = toml.load(config_path)
    defaults = _default_config_dict()
    merged = _merge_dicts(defaults, data)
    merged = _apply_env_overrides(merged)
    return OmnivocalConfig.from_dict(merged)


def save_config(config: Dict[str, Any] | OmnivocalConfig, path: Path | None = None) -> None:
    config_path = path or CONFIG_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)
    data = config.to_dict() if isinstance(config, OmnivocalConfig) else config
    with config_path.open("w", encoding="utf-8") as fh:
        toml.dump(data, fh)


def get_config_value(config: OmnivocalConfig, key: str) -> Any:
    section_name, option_name = _split_key(key)
    section = getattr(config, section_name)
    return getattr(section, option_name)


def set_config_value(config: OmnivocalConfig, key: str, value: str) -> OmnivocalConfig:
    section_name, option_name = _split_key(key)
    section = getattr(config, section_name)
    current_value = getattr(section, option_name)
    coerced = _coerce(value, current_value)
    setattr(section, option_name, coerced)
    return config


def _split_key(key: str) -> tuple[str, str]:
    if "." not in key:
        raise ValueError("Key must be in section.option format")
    section, option = key.split(".", 1)
    if not section or not option:
        raise ValueError("Invalid configuration key")
    return section, option


def _merge_dicts(defaults: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    merged = defaults.copy()
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_dicts(merged[key], value)
        else:
            merged[key] = value
    return merged


def _apply_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
    overrides: Dict[str, Any] = {}
    prefix = f"{ENV_PREFIX}_"
    for env_key, env_value in os.environ.items():
        if not env_key.startswith(prefix):
            continue
        path = env_key[len(prefix) :].lower().split("_")
        if len(path) < 2:
            continue
        section = path[0]
        option = "_".join(path[1:])
        try:
            current = config[section][option]
            config[section][option] = _coerce(env_value, current)
        except (KeyError, ValueError):
            continue
    return config


__all__ = [
    "CONFIG_PATH",
    "CONFIG_DIR",
    "OmnivocalConfig",
    "load_config",
    "save_config",
    "set_config_value",
    "get_config_value",
    "ensure_config",
]
