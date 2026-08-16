#!/usr/bin/env python3
"""Distinct research build system — NOT PackageBuilder / NOT godot_pack_v1.

Parses experiment.toml, runs seeded deterministic trial, emits provenance artifact.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path

BUILD_SYSTEM = "research_pipeline_v1"


def _parse_toml_lite(text: str) -> dict:
    out: dict = {"experiment": {}}
    section = None
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip()
            out.setdefault(section, {})
            continue
        if "=" not in line or section is None:
            continue
        k, v = [x.strip() for x in line.split("=", 1)]
        if v.lower() in ("true", "false"):
            val: object = v.lower() == "true"
        elif re.fullmatch(r"-?\d+", v):
            val = int(v)
        elif v.startswith('"') and v.endswith('"'):
            val = v[1:-1]
        else:
            val = v
        out[section][k] = val
    return out


def run_experiment(app_dir: Path, out_dir: Path, *, mutate: str | None = None) -> dict:
    app_dir = Path(app_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cfg_path = app_dir / "experiment.toml"
    cfg = _parse_toml_lite(cfg_path.read_text(encoding="utf-8"))
    exp = dict(cfg.get("experiment") or {})
    if mutate:
        exp["hypothesis"] = f"{exp.get('hypothesis','')} | mutate={mutate}"
    seed = int(exp.get("seed", 0))
    n = int(exp.get("samples", 8))
    # Deterministic LCG samples — no numpy dependency in guest.
    x = seed & 0xFFFFFFFF
    samples = []
    for _ in range(n):
        x = (1664525 * x + 1013904223) & 0xFFFFFFFF
        samples.append(x / 0xFFFFFFFF)
    mean = sum(samples) / len(samples)
    body = {
        "schema": "gunnchos.research_artifact.v1",
        "build_system": BUILD_SYSTEM,
        "experiment": exp,
        "mean": mean,
        "n": n,
        "EXTERNAL_REPRODUCTION": False,
        "SILICON_EXACT_EMULATION": False,
        "built_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    raw = json.dumps(body, sort_keys=True).encode()
    body["artifact_sha256"] = hashlib.sha256(raw).hexdigest()
    out = out_dir / "RESULT.json"
    out.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")
    body["ok"] = True
    body["artifact_path"] = str(out)
    return body


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    print(json.dumps(run_experiment(root, root / "out"), indent=2))
