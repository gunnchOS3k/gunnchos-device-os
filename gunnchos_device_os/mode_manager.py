"""Mode manager — loads policies from config/modes.yaml."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "modes.yaml"


@lru_cache(maxsize=1)
def _load_modes() -> dict[str, dict[str, Any]]:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")).get("modes", {})


def list_modes() -> tuple[str, ...]:
    return tuple(_load_modes().keys())


MODES: tuple[str, ...] = list_modes()


def get_mode_policy(mode: str) -> dict[str, Any]:
    modes = _load_modes()
    if mode not in modes:
        raise ValueError(f"Unknown mode: {mode}")
    return {"mode": mode, **modes[mode]}
