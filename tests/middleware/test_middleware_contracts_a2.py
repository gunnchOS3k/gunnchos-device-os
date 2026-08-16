"""Stream A A2 middleware contract schema tests."""
from __future__ import annotations

import json
from pathlib import Path

from gunnchos_device_os.middleware.contracts import (
    CONTRACT_SCHEMA_FILES,
    INVENTORY_PATH,
    load_example,
    load_inventory,
    validate_all_examples,
    validate_payload,
)
from gunnchos_device_os.release_engineering.sdk.manifest import validate_manifest

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_inventory_lists_six_priority_contracts():
    inv = load_inventory()
    assert inv["schema"] == "gunnchos.middleware.contract_inventory.v1"
    ids = [c["id"] for c in inv["contracts"]]
    assert ids == [
        "MW-IDENTITY",
        "MW-PACKAGE",
        "MW-RING-INPUT",
        "MW-AI-INTERFACE",
        "MW-GAME-LAUNCH",
        "MW-SESSION-CONTINUITY",
    ]
    assert INVENTORY_PATH.exists()


def test_all_examples_validate():
    report = validate_all_examples()
    assert report["ok"] is True, report


def test_identity_example_validates():
    assert validate_payload("MW-IDENTITY", load_example("MW-IDENTITY")) == []


def test_package_example_validates():
    example = load_example("MW-PACKAGE")
    assert validate_payload("MW-PACKAGE", example) == []
    assert validate_manifest(example) == []


def test_ring_input_example_validates():
    example = load_example("MW-RING-INPUT")
    assert example["SILICON_EXACT_EMULATION"] is False
    assert example["PHYSICAL_RING_E6"] is False
    assert validate_payload("MW-RING-INPUT", example) == []


def test_ai_interface_example_validates():
    assert validate_payload("MW-AI-INTERFACE", load_example("MW-AI-INTERFACE")) == []


def test_game_launch_example_validates():
    example = load_example("MW-GAME-LAUNCH")
    assert example["SILICON_EXACT_EMULATION"] is False
    assert validate_payload("MW-GAME-LAUNCH", example) == []


def test_session_continuity_example_validates():
    assert validate_payload("MW-SESSION-CONTINUITY", load_example("MW-SESSION-CONTINUITY")) == []


def test_ring_schema_rejects_silicon_exact_true():
    bad = dict(load_example("MW-RING-INPUT"))
    bad["SILICON_EXACT_EMULATION"] = True
    errs = validate_payload("MW-RING-INPUT", bad)
    assert errs


def test_schema_files_on_disk():
    for name in CONTRACT_SCHEMA_FILES.values():
        path = REPO_ROOT / "shared_contracts" / "middleware" / "schemas" / name
        assert path.exists(), path
        json.loads(path.read_text(encoding="utf-8"))
