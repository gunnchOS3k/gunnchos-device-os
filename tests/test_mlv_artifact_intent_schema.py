from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "shared_contracts" / "mlv_artifact_intent.schema.json").read_text(encoding="utf-8"))


def _validate(payload: dict) -> list[str]:
    errors: list[str] = []
    required = SCHEMA["required"]
    for key in required:
        if key not in payload:
            errors.append(f"missing {key}")
    if payload.get("default_visibility") != "private":
        errors.append("default_visibility must be private")
    extra = set(payload) - set(SCHEMA["properties"])
    if extra:
        errors.append(f"unknown fields {sorted(extra)}")
    return errors


def test_schema_rejects_public_default():
    errors = _validate(
        {
            "artifact_id": "art-1",
            "owner_id": "owner-1",
            "title": "report.pdf",
            "mime_type": "application/pdf",
            "app_id": "waike_learning_os",
            "default_visibility": "public",
        }
    )
    assert errors


def test_schema_accepts_private_intent():
    errors = _validate(
        {
            "artifact_id": "art-1",
            "owner_id": "owner-1",
            "title": "report.pdf",
            "mime_type": "application/pdf",
            "app_id": "waike_learning_os",
            "local_uri": "file://tmp/report.pdf",
            "cloud_node_id": None,
            "suggested_presentation": "book",
            "default_visibility": "private",
        }
    )
    assert errors == []
