"""Load and validate the pinned gunnchAI3k ↔ device-os compatibility contract."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import jsonschema

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "cross_repo_gunnchai_bridge" / "GUNNCHAI_COMPAT_CONTRACT.json"
SCHEMA_PATH = ROOT / "schemas" / "gunnchai_compat_contract.schema.json"


def load_contract(path: Path | None = None) -> dict[str, Any]:
    target = path or CONTRACT_PATH
    return json.loads(target.read_text(encoding="utf-8"))


def validate_contract(doc: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = doc if doc is not None else load_contract()
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(instance=payload, schema=schema)
    assumptions = payload["device_os_assumptions"]
    if assumptions.get("GUNNCHAI_APP_PRODUCT_COMPLETE") is not False:
        raise ValueError("contract must keep GUNNCHAI_APP_PRODUCT_COMPLETE false")
    if payload["coupling_policy"].get("blocks_device_os_ci") is not False:
        raise ValueError("contract must not block device-os CI")
    if payload["evidence_class"] != "ACCEPTED_MAIN":
        raise ValueError("contract evidence_class must be ACCEPTED_MAIN")
    return {"ok": True, "contract_version": payload["contract_version"]}


def _git_sha(repo: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def discover_gunnchai_sibling(device_os_root: Path | None = None) -> Path | None:
    root = Path(device_os_root or ROOT).resolve()
    for parent in (root.parent, root.parent.parent):
        cand = parent / "gunnchAI3k"
        if (cand / "package.json").is_file():
            return cand
    return None


def verify_owner_artifacts(
    device_os_root: Path | None = None,
    gunnchai_root: Path | None = None,
) -> dict[str, Any]:
    """Optional sibling check — ACCEPTED_MAIN evidence when sibling matches pin."""
    contract = load_contract(Path(device_os_root or ROOT) / CONTRACT_PATH.relative_to(ROOT))
    pinned = contract["gunnchai"]["accepted_main_sha"]
    sibling = Path(gunnchai_root) if gunnchai_root else discover_gunnchai_sibling(device_os_root)
    out: dict[str, Any] = {
        "schema": "gunnchos.gunnchai_compat_sibling_verify.v1",
        "evidence_class": "ACCEPTED_MAIN",
        "pinned_gunnchai_sha": pinned,
        "sibling_present": sibling is not None,
        "sha_match": False,
        "artifacts_ok": False,
        "artifact_checks": [],
        "ok": False,
    }
    if sibling is None:
        out["note"] = "Sibling gunnchAI3k absent — pin-file contract still valid; run locally with sibling checkout."
        return out

    live_sha = _git_sha(sibling)
    out["live_sha"] = live_sha
    out["sha_match"] = live_sha == pinned
    checks: list[dict[str, Any]] = []
    artifacts_ok = True
    for rel in contract["gunnchai"]["owner_artifacts"]:
        path = sibling / rel
        present = path.is_file()
        checks.append({"path": rel, "present": present})
        artifacts_ok = artifacts_ok and present

    out["artifact_checks"] = checks
    out["artifacts_ok"] = artifacts_ok

    completion: dict[str, Any] = {}
    completion_path = sibling / "artifacts/product_completion/PRODUCT_COMPLETION_RESULT.json"
    if completion_path.is_file():
        doc = json.loads(completion_path.read_text(encoding="utf-8"))
        tokens = doc.get("tokens") or {}
        completion = {
            "GUNNCHAI_DIGITAL_PRODUCT_CAPABILITY_PASS": tokens.get(
                "GUNNCHAI_DIGITAL_PRODUCT_CAPABILITY_PASS"
            ),
            "GUNNCHAI_APP_PRODUCT_COMPLETE": tokens.get("GUNNCHAI_APP_PRODUCT_COMPLETE"),
        }
    out["completion_tokens"] = completion

    expected = contract["device_os_assumptions"]
    token_ok = completion.get("GUNNCHAI_DIGITAL_PRODUCT_CAPABILITY_PASS") == expected.get(
        "GUNNCHAI_DIGITAL_PRODUCT_CAPABILITY_PASS"
    ) and completion.get("GUNNCHAI_APP_PRODUCT_COMPLETE") == expected.get(
        "GUNNCHAI_APP_PRODUCT_COMPLETE"
    )

    out["token_assumptions_match"] = token_ok if completion else None
    out["ok"] = out["sha_match"] and artifacts_ok and (token_ok if completion else False)
    return out
