"""Scan source trees for SBOM/HBOM/AI-BOM inventory inputs."""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

import yaml


UNKNOWN = "UNKNOWN"
BLOCKING = "UNKNOWN_RELEASE_BLOCKING"

REQ_LINE = re.compile(r"^([A-Za-z0-9_.-]+)(?:\[[^\]]+\])?\s*([>=<!~].+)?$")


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _load_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def load_provenance_map(repo_root: Path) -> dict[str, dict[str, Any]]:
    path = repo_root / "compliance" / "legal" / "COMPONENT_PROVENANCE.yaml"
    data = _load_yaml(path) if path.exists() else None
    entries = (data or {}).get("components") or []
    out: dict[str, dict[str, Any]] = {}
    for row in entries:
        key = str(row.get("id") or row.get("name") or "").strip().lower()
        if key:
            out[key] = row
    return out


def _component(
    *,
    kind: str,
    name: str,
    source: str,
    version: str | None = None,
    license_id: str | None = None,
    provenance: str | None = None,
    extra: dict[str, Any] | None = None,
    known: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    meta = (known or {}).get(name.lower(), {})
    lic = license_id or meta.get("license") or UNKNOWN
    prov = provenance or meta.get("provenance") or UNKNOWN
    blocking = lic == UNKNOWN or prov == UNKNOWN
    row = {
        "kind": kind,
        "name": name,
        "version": version or meta.get("version") or UNKNOWN,
        "license": lic,
        "provenance": prov,
        "source": source,
        "release_status": BLOCKING if blocking else "inventoried",
        "unknown_release_blocking": blocking,
    }
    if extra:
        row.update(extra)
    return row


def scan_python_requirements(repo_root: Path, known: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for fname in ("requirements.txt", "requirements-dev.txt"):
        path = repo_root / fname
        if not path.exists():
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            m = REQ_LINE.match(line)
            if not m:
                rows.append(
                    _component(
                        kind="python",
                        name=line,
                        source=str(path.relative_to(repo_root)),
                        known=known,
                    )
                )
                continue
            name, spec = m.group(1), (m.group(2) or "").strip()
            rows.append(
                _component(
                    kind="python",
                    name=name,
                    version=spec or UNKNOWN,
                    source=str(path.relative_to(repo_root)),
                    known=known,
                )
            )
    return rows


def scan_npm(repo_root: Path, known: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pkg in repo_root.rglob("package.json"):
        rel = str(pkg.relative_to(repo_root))
        if any(p in rel for p in ("node_modules", ".git", "artifacts/", "results/")):
            continue
        data = _load_json(pkg) or {}
        for section in ("dependencies", "devDependencies"):
            deps = data.get(section) or {}
            if not isinstance(deps, dict):
                continue
            for name, ver in deps.items():
                rows.append(
                    _component(
                        kind="npm",
                        name=str(name),
                        version=str(ver),
                        source=rel,
                        extra={"section": section},
                        known=known,
                    )
                )
    return rows


def scan_godot_addons(roots: list[Path], known: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for root in roots:
        if not root.exists():
            continue
        for cfg in root.rglob("plugin.cfg"):
            rel = str(cfg)
            if "addons" not in cfg.parts:
                continue
            text = cfg.read_text(encoding="utf-8", errors="replace")
            name = next(
                (ln.split("=", 1)[1].strip().strip('"') for ln in text.splitlines() if ln.strip().startswith("name=")),
                cfg.parent.name,
            )
            rows.append(
                _component(
                    kind="godot_addon",
                    name=name,
                    source=rel,
                    extra={"plugin_cfg": rel},
                    known=known,
                )
            )
    return rows


def scan_fonts_media(repo_root: Path, known: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    exts = {".ttf", ".otf", ".woff", ".woff2", ".ogg", ".mp3", ".wav", ".png", ".jpg", ".jpeg"}
    skip = {"node_modules", ".git", "artifacts", "results", "__pycache__"}
    for path in repo_root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in exts:
            continue
        if any(p in skip for p in path.parts):
            continue
        sidecar = path.with_suffix(path.suffix + ".license")
        alt = path.parent / "LICENSE"
        lic = UNKNOWN
        prov = UNKNOWN
        if sidecar.exists():
            lic = sidecar.read_text(encoding="utf-8").strip().splitlines()[0][:80]
            prov = str(sidecar.relative_to(repo_root))
        elif alt.exists():
            lic = "SEE_DIRECTORY_LICENSE"
            prov = str(alt.relative_to(repo_root))
        rows.append(
            _component(
                kind="font" if path.suffix.lower() in {".ttf", ".otf", ".woff", ".woff2"} else "media",
                name=path.name,
                source=str(path.relative_to(repo_root)),
                license_id=lic if lic != UNKNOWN else None,
                provenance=prov if prov != UNKNOWN else None,
                known=known,
            )
        )
    return rows


def scan_ai_models(roots: list[Path], known: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    names = ("manifest.json", "registry.json", "MODEL_CARD.json", "model_card.json")
    for root in roots:
        if not root.exists():
            continue
        for fname in names:
            for path in root.rglob(fname):
                if any(p in path.parts for p in ("node_modules", ".git", "artifacts")):
                    continue
                data = _load_json(path)
                if data is None:
                    continue
                models = []
                if isinstance(data, dict) and "id" in data and ("license" in data or "sha256" in data):
                    models = [data]
                elif isinstance(data, dict):
                    for key, val in data.items():
                        if isinstance(val, dict) and ("model_id" in val or "sha256" in val or "license" in val):
                            models.append({"name": key, **val})
                for model in models:
                    name = str(model.get("id") or model.get("model_id") or model.get("name") or path.stem)
                    rows.append(
                        _component(
                            kind="ai_model",
                            name=name,
                            version=str(model.get("quant") or model.get("version") or UNKNOWN),
                            license_id=model.get("license") or model.get("license_id"),
                            provenance=model.get("ggufSource")
                            or model.get("modelCard")
                            or model.get("path")
                            or str(path),
                            source=str(path),
                            extra={
                                "sha256": model.get("sha256"),
                                "weights_committed_to_git": model.get("weightsCommittedToGit"),
                            },
                            known=known,
                        )
                    )
    return rows


def scan_datasets_science(roots: list[Path], known: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for root in roots:
        if not root.exists():
            continue
        for path in list(root.rglob("manifest.json")) + list(root.rglob("*provenance*")):
            if path.suffix.lower() not in {".json", ".csv", ".yaml", ".yml"}:
                continue
            if any(p in path.parts for p in ("node_modules", ".git")):
                continue
            data = _load_json(path) if path.suffix == ".json" else _load_yaml(path)
            kind = "scientific" if "archive" in str(path).lower() or "science" in str(path).lower() else "dataset"
            name = path.name
            lic = None
            prov = str(path)
            if isinstance(data, dict):
                lic = data.get("license") or (data.get("rights") or {}).get("license")
                if data.get("description"):
                    name = str(data.get("snapshotId") or data.get("id") or path.stem)
            rows.append(
                _component(
                    kind=kind,
                    name=str(name),
                    source=str(path),
                    license_id=lic,
                    provenance=prov,
                    known=known,
                )
            )
    return rows


def scan_hardware_bom(roots: list[Path], known: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*.csv"):
            if "bom" not in path.name.lower() and "bom" not in str(path.parent).lower():
                continue
            try:
                with path.open(encoding="utf-8", newline="") as fh:
                    reader = csv.DictReader(fh)
                    for rec in reader:
                        mpn = rec.get("MPN") or rec.get("mpn") or rec.get("part") or ""
                        mfr = rec.get("manufacturer") or rec.get("Manufacturer") or ""
                        name = f"{mfr}:{mpn}".strip(":") or rec.get("description") or path.stem
                        prov = rec.get("datasheet_or_docs") or rec.get("status") or UNKNOWN
                        rows.append(
                            _component(
                                kind="hardware",
                                name=str(name),
                                source=str(path),
                                license_id="hardware_component",
                                provenance=None if prov in ("", UNKNOWN, "CONTACT_VENDOR") else str(prov),
                                extra={"mpn": mpn, "manufacturer": mfr},
                                known=known,
                            )
                        )
            except Exception:
                rows.append(
                    _component(kind="hardware", name=path.name, source=str(path), known=known)
                )
    return rows
