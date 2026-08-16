"""Middleware contract inventory helpers (Stream A A2)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
MIDDLEWARE_ROOT = REPO_ROOT / "shared_contracts" / "middleware"
SCHEMAS_DIR = MIDDLEWARE_ROOT / "schemas"
EXAMPLES_DIR = MIDDLEWARE_ROOT / "examples"
INVENTORY_PATH = MIDDLEWARE_ROOT / "INVENTORY.json"

CONTRACT_SCHEMA_FILES = {
    "MW-IDENTITY": "identity.v1.schema.json",
    "MW-PACKAGE": "package_manifest.v1.schema.json",
    "MW-RING-INPUT": "ring_input.v1.schema.json",
    "MW-AI-INTERFACE": "ai_interface.v1.schema.json",
    "MW-GAME-LAUNCH": "game_launch.v1.schema.json",
    "MW-SESSION-CONTINUITY": "session_continuity.v1.schema.json",
}

EXAMPLE_FILES = {
    "MW-IDENTITY": "identity.example.json",
    "MW-PACKAGE": "package_manifest.example.json",
    "MW-RING-INPUT": "ring_input.example.json",
    "MW-AI-INTERFACE": "ai_interface.example.json",
    "MW-GAME-LAUNCH": "game_launch.example.json",
    "MW-SESSION-CONTINUITY": "session_continuity.example.json",
}


def load_inventory() -> dict[str, Any]:
    return json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))


def load_schema(contract_id: str) -> dict[str, Any]:
    name = CONTRACT_SCHEMA_FILES[contract_id]
    return json.loads((SCHEMAS_DIR / name).read_text(encoding="utf-8"))


def load_example(contract_id: str) -> dict[str, Any]:
    name = EXAMPLE_FILES[contract_id]
    return json.loads((EXAMPLES_DIR / name).read_text(encoding="utf-8"))


def validate_payload(contract_id: str, payload: dict[str, Any]) -> list[str]:
    schema = load_schema(contract_id)
    validator = Draft202012Validator(schema)
    return sorted(e.message for e in validator.iter_errors(payload))


def validate_all_examples() -> dict[str, Any]:
    results: dict[str, Any] = {}
    for contract_id in CONTRACT_SCHEMA_FILES:
        errs = validate_payload(contract_id, load_example(contract_id))
        results[contract_id] = {"ok": not errs, "errors": errs}
    return {
        "ok": all(v["ok"] for v in results.values()),
        "contracts": results,
        "inventory_path": str(INVENTORY_PATH),
    }
