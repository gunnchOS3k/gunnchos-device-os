"""Reproducibility evaluation — pinned env, no laptop-only secrets/paths."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import os
import re
import yaml

from gunnchos_device_os.cont_viii import CLAIM_BOUNDARY, TOKEN_REPRO_PASS

FORBIDDEN_PATH_RE = re.compile(
    r"(/Users/[A-Za-z0-9._-]+|/home/edmund|C:\\\\Users\\\\Edmund|/Users/gunnchos/Library)",
    re.I,
)
SECRET_NAME_RE = re.compile(r"(api[_-]?key|private[_-]?key|secret|password|token)", re.I)


def evaluate_reproducibility(root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[2]
    manifest_path = root / "REPRODUCIBILITY_MANIFEST.yaml"
    devcontainer = root / ".devcontainer/devcontainer.json"
    makefile = root / "Makefile"
    checks = {
        "manifest_present": manifest_path.exists(),
        "devcontainer_present": devcontainer.exists(),
        "makefile_bootstrap": False,
        "makefile_build": False,
        "makefile_test": False,
        "makefile_package": False,
        "makefile_evidence": False,
        "no_laptop_only_paths": True,
        "no_embedded_prod_secrets": True,
    }
    details: dict[str, Any] = {}
    if makefile.exists():
        mk = makefile.read_text(encoding="utf-8")
        for target in ("bootstrap", "build", "test", "package", "evidence"):
            checks[f"makefile_{target}"] = bool(
                re.search(rf"^{target}\s*:", mk, re.M)
                or re.search(rf"^\.PHONY:.*\b{target}\b", mk, re.M)
            )
    laptop_hits = []
    secret_hits = []
    scan_files = [
        manifest_path,
        devcontainer,
        root / "sdk/.env.example",
        root / "config/productivity/stack.yaml",
    ]
    for path in scan_files:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for m in FORBIDDEN_PATH_RE.finditer(text):
            laptop_hits.append({"path": str(path.relative_to(root)), "match": m.group(0)})
        if path.name.endswith(".example") or path.suffix in {".yaml", ".yml", ".json", ".md"}:
            # .env.example may name SECRET vars but must not contain values
            if path.name == ".env.example":
                for line in text.splitlines():
                    if "=" in line and not line.strip().startswith("#"):
                        k, _, v = line.partition("=")
                        if SECRET_NAME_RE.search(k) and v.strip() and v.strip() not in {"", "changeme", "REPLACE_ME", "<unset>"}:
                            if not v.strip().startswith("<") and v.strip().upper() not in {"REPLACE_ME", "CHANGEME", "UNSET"}:
                                # allow empty or placeholder
                                if len(v.strip()) > 12 and "replace" not in v.lower() and "your-" not in v.lower():
                                    secret_hits.append({"path": str(path.relative_to(root)), "key": k.strip()})
    checks["no_laptop_only_paths"] = len(laptop_hits) == 0
    checks["no_embedded_prod_secrets"] = len(secret_hits) == 0
    details["laptop_hits"] = laptop_hits
    details["secret_hits"] = secret_hits

    manifest = {}
    if manifest_path.exists():
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
        checks["manifest_pinned_python"] = bool(manifest.get("python"))
        checks["manifest_pinned_node"] = bool(manifest.get("node"))
        checks["manifest_claims_no_host_secrets"] = bool(manifest.get("no_host_secrets", True))
    else:
        checks["manifest_pinned_python"] = False
        checks["manifest_pinned_node"] = False
        checks["manifest_claims_no_host_secrets"] = False

    required = [k for k, v in checks.items() if k.startswith("makefile_") or k in {
        "manifest_present", "devcontainer_present", "no_laptop_only_paths",
        "no_embedded_prod_secrets", "manifest_pinned_python", "manifest_claims_no_host_secrets",
    }]
    ok = all(checks[k] for k in required)
    return {
        "schema": "gunnchos.reproducibility.v1",
        "ok": ok,
        "token": TOKEN_REPRO_PASS if ok else None,
        "checks": checks,
        "details": details,
        "manifest_keys": sorted(manifest.keys()) if isinstance(manifest, dict) else [],
        "host_env_leaked": bool(os.environ.get("GUNNCHOS_HOST_ONLY_SECRET")),
        "mock": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
