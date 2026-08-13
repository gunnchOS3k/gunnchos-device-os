"""Assemble SBOM / HBOM / AI-BOM documents and release-blocking rollup."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from gunnchos_device_os.digital_inventory.rights import (
    check_ai_model_licenses,
    check_archive_provenance,
    check_beatlink,
)
from gunnchos_device_os.digital_inventory.scanner import (
    BLOCKING,
    load_provenance_map,
    scan_ai_models,
    scan_datasets_science,
    scan_fonts_media,
    scan_godot_addons,
    scan_hardware_bom,
    scan_npm,
    scan_python_requirements,
)


CLAIM_BOUNDARY = (
    "Digital inventory of declared components. UNKNOWN_RELEASE_BLOCKING is a "
    "machine gate, not a legal clearance. Legal approval remains HUMAN/EXTERNAL. "
    "Does not claim SPDX/CycloneDX certification or complete supply-chain audit."
)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sibling(repo_root: Path, name: str) -> Path | None:
    cand = repo_root.parent / name
    return cand if cand.exists() else None


def collect_components(repo_root: Path) -> list[dict[str, Any]]:
    known = load_provenance_map(repo_root)
    roots = [
        repo_root,
        sibling(repo_root, "gunnchAI3k"),
        sibling(repo_root, "beatlink-party"),
        sibling(repo_root, "archive-of-life-artifact-world"),
        sibling(repo_root, "pedestrian-pursuit"),
        sibling(repo_root, "anime-aggressors"),
        sibling(repo_root, "gunnchos-7gc-ai-ran-field-kit"),
        sibling(repo_root, "gunnchos-hardware-industrial-design"),
    ]
    present = [p for p in roots if p is not None]
    components: list[dict[str, Any]] = []
    components.extend(scan_python_requirements(repo_root, known))
    components.extend(scan_npm(repo_root, known))
    components.extend(scan_godot_addons(present, known))
    components.extend(scan_fonts_media(repo_root, known))
    ai_roots = [
        p
        for p in (
            repo_root,
            sibling(repo_root, "gunnchAI3k"),
        )
        if p is not None
    ]
    science_roots = [
        p
        for p in (
            sibling(repo_root, "archive-of-life-artifact-world"),
            sibling(repo_root, "beatlink-party"),
        )
        if p is not None
    ]
    components.extend(scan_ai_models(ai_roots, known))
    components.extend(scan_datasets_science(science_roots, known))
    hbom_roots = [
        p
        for p in (
            sibling(repo_root, "gunnchos-7gc-ai-ran-field-kit"),
            sibling(repo_root, "gunnchos-hardware-industrial-design"),
        )
        if p is not None
    ]
    components.extend(scan_hardware_bom(hbom_roots, known))
    # First-party repo itself
    components.insert(
        0,
        {
            "kind": "source",
            "name": "gunnchos-device-os",
            "version": "HEAD",
            "license": known.get("gunnchos-device-os", {}).get("license", "MIT"),
            "provenance": "first_party",
            "source": ".",
            "release_status": "inventoried",
            "unknown_release_blocking": False,
        },
    )
    return components


def to_cyclonedx(components: list[dict[str, Any]]) -> dict[str, Any]:
    cdx = []
    type_map = {
        "python": "library",
        "npm": "library",
        "godot_addon": "library",
        "font": "file",
        "media": "file",
        "ai_model": "machine-learning-model",
        "dataset": "data",
        "scientific": "data",
        "hardware": "device",
        "source": "application",
    }
    for c in components:
        cdx.append(
            {
                "type": type_map.get(str(c.get("kind")), "library"),
                "name": c.get("name"),
                "version": c.get("version"),
                "licenses": [{"license": {"id": c.get("license")}}] if c.get("license") else [],
                "properties": [
                    {"name": "gunnchos:kind", "value": str(c.get("kind"))},
                    {"name": "gunnchos:provenance", "value": str(c.get("provenance"))},
                    {"name": "gunnchos:release_status", "value": str(c.get("release_status"))},
                    {"name": "gunnchos:source", "value": str(c.get("source"))},
                ],
            }
        )
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "component": {"name": "gunnchos-device-os", "type": "operating-system"},
            "properties": [{"name": "gunnchos:claim_boundary", "value": CLAIM_BOUNDARY}],
        },
        "components": cdx,
    }


def split_boms(components: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    sbom_kinds = {"source", "python", "npm", "godot_addon", "font", "media"}
    return {
        "sbom": [c for c in components if c.get("kind") in sbom_kinds],
        "hbom": [c for c in components if c.get("kind") == "hardware"],
        "ai_bom": [c for c in components if c.get("kind") in {"ai_model", "dataset", "scientific"}],
    }


def build_inventory(repo_root: Path) -> dict[str, Any]:
    components = collect_components(repo_root)
    boms = split_boms(components)
    blocking = [c for c in components if c.get("unknown_release_blocking")]
    beatlink = check_beatlink(sibling(repo_root, "beatlink-party"))
    archive = check_archive_provenance(sibling(repo_root, "archive-of-life-artifact-world"))
    ai_lic = check_ai_model_licenses(components)
    rights_blocking = list(beatlink.get("blocking") or []) + list(archive.get("blocking") or [])
    document = {
        "schema": "gunnchos.digital_inventory.v1",
        "claim_boundary": CLAIM_BOUNDARY,
        "legal_approval": "HUMAN/EXTERNAL",
        "EXTERNAL_PENTEST_COMPLETE": False,
        "unknown_release_blocking_count": len(blocking) + len(rights_blocking),
        "UNKNOWN_RELEASE_BLOCKING": bool(blocking or rights_blocking),
        "counts": {
            "components": len(components),
            "sbom": len(boms["sbom"]),
            "hbom": len(boms["hbom"]),
            "ai_bom": len(boms["ai_bom"]),
            "blocking": len(blocking),
        },
        "components": components,
        "boms": boms,
        "rights": {
            "beatlink": beatlink,
            "archive": archive,
            "ai_models": ai_lic,
        },
        "release_gate": {
            "may_ship": False,
            "reason": "UNKNOWN_RELEASE_BLOCKING or HUMAN/EXTERNAL legal pending",
            "legal_approval": "HUMAN/EXTERNAL",
        },
    }
    document["document_sha256"] = _sha256_text(json.dumps(document, sort_keys=True, default=str))
    return document


def write_inventory(repo_root: Path, dest_dir: Path) -> dict[str, Any]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    inventory = build_inventory(repo_root)
    (dest_dir / "DIGITAL_INVENTORY.json").write_text(
        json.dumps(inventory, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )
    (dest_dir / "sbom.cdx.json").write_text(
        json.dumps(to_cyclonedx(inventory["boms"]["sbom"]), indent=2) + "\n", encoding="utf-8"
    )
    (dest_dir / "hbom.json").write_text(
        json.dumps({"schema": "gunnchos.hbom.v1", "components": inventory["boms"]["hbom"]}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    (dest_dir / "ai_bom.json").write_text(
        json.dumps({"schema": "gunnchos.ai_bom.v1", "components": inventory["boms"]["ai_bom"]}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    blocking = [c for c in inventory["components"] if c.get("unknown_release_blocking")]
    lines = [
        "# Digital inventory",
        "",
        f"UNKNOWN_RELEASE_BLOCKING: `{inventory['UNKNOWN_RELEASE_BLOCKING']}`",
        f"Blocking count: {inventory['unknown_release_blocking_count']}",
        f"Legal approval: {inventory['legal_approval']}",
        "",
        CLAIM_BOUNDARY,
        "",
        "## Counts",
        "",
        json.dumps(inventory["counts"], indent=2),
        "",
        "## Blocking sample",
        "",
    ]
    for row in blocking[:40]:
        lines.append(f"- {row.get('kind')} `{row.get('name')}` license={row.get('license')} provenance={row.get('provenance')}")
    (dest_dir / "INVENTORY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return inventory
