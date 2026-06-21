"""Load user-focused OS YAML configuration files."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"


def _load(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing config: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


@lru_cache(maxsize=1)
def load_personas() -> dict[str, Any]:
    return _load(CONFIG_DIR / "personas.yaml")


@lru_cache(maxsize=1)
def load_journey_presets() -> dict[str, Any]:
    return _load(CONFIG_DIR / "journey_presets.yaml")


@lru_cache(maxsize=1)
def load_app_packs() -> dict[str, Any]:
    return _load(CONFIG_DIR / "app_packs.yaml")


@lru_cache(maxsize=1)
def load_themes() -> dict[str, Any]:
    return _load(CONFIG_DIR / "themes.yaml")


@lru_cache(maxsize=1)
def load_workspaces() -> dict[str, Any]:
    return _load(CONFIG_DIR / "workspaces.yaml")


@lru_cache(maxsize=1)
def load_accessibility_defaults() -> dict[str, Any]:
    return _load(CONFIG_DIR / "accessibility_defaults.yaml")


@lru_cache(maxsize=1)
def load_edge_cases() -> dict[str, Any]:
    return _load(CONFIG_DIR / "edge_cases.yaml")


def clear_cache() -> None:
    load_personas.cache_clear()
    load_journey_presets.cache_clear()
    load_app_packs.cache_clear()
    load_themes.cache_clear()
    load_workspaces.cache_clear()
    load_accessibility_defaults.cache_clear()
    load_edge_cases.cache_clear()
