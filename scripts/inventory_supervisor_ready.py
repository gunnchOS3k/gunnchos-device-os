#!/usr/bin/env python3
"""Inventory remaining mock:/stub markers and PHYSICAL_PENDING tokens from source."""
from __future__ import annotations

import ast
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PHYSICAL_TOKENS = (
    "PHYSICAL_PENDING",
    "GUNNCHOS_PHYSICAL_BOOT_PENDING",
    "OS_PHYSICAL_BOOT_PENDING",
    "GUNNCHOS_PHYSICAL_SYSTEM_IMAGE_PENDING",
    "PHYSICAL_EXECUTION_FREEZE",
    "GUNNCHOS_PHYSICAL_DOCK_PENDING",
)

SKIP_DIRS = {
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "dist",
}


def _iter_files(*suffixes: str) -> list[Path]:
    out: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix in suffixes or path.name in {"Makefile", "Dockerfile"}:
            out.append(path)
    return out


def audit_python_mocks() -> list[dict[str, str | int]]:
    """AST-scan for mock True literals assigned in dicts / keywords."""
    hits: list[dict[str, str | int]] = []
    for path in _iter_files(".py"):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError:
            continue
        rel = str(path.relative_to(ROOT))
        for node in ast.walk(tree):
            if isinstance(node, ast.keyword) and node.arg == "mock":
                if isinstance(node.value, ast.Constant) and node.value.value is True:
                    hits.append({"file": rel, "line": node.lineno, "kind": "kw_mock_true"})
            if isinstance(node, ast.Dict):
                for key, val in zip(node.keys, node.values):
                    if isinstance(key, ast.Constant) and key.value == "mock":
                        if isinstance(val, ast.Constant) and val.value is True:
                            hits.append({"file": rel, "line": val.lineno, "kind": "dict_mock_true"})
    return hits


def inventory_physical() -> dict[str, list[str]]:
    by_token: dict[str, list[str]] = defaultdict(list)
    pattern = re.compile("|".join(re.escape(t) for t in PHYSICAL_TOKENS))
    for path in _iter_files(".py", ".md", ".yml", ".yaml", ".json"):
        rel = str(path.relative_to(ROOT))
        if rel.startswith("artifacts/") and "supervisor_ready" not in rel:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        found = sorted(set(pattern.findall(text)))
        for token in found:
            by_token[token].append(rel)
    return {k: sorted(set(v)) for k, v in sorted(by_token.items())}


def write_reports() -> dict:
    mocks = audit_python_mocks()
    physical = inventory_physical()
    out = ROOT / "artifacts" / "supervisor_ready"
    out.mkdir(parents=True, exist_ok=True)
    mock_payload = {
        "schema": "gunnchos.mock_audit.v1",
        "claim": (
            "Remaining mock:True markers in Python. Launcher mock UI and "
            "Edge-IO session export stay labeled mock. Not a retirement of hardware mocks."
        ),
        "count": len(mocks),
        "hits": mocks,
    }
    (out / "MOCK_AUDIT.json").write_text(
        json.dumps(mock_payload, indent=2) + "\n", encoding="utf-8"
    )
    phys_payload = {
        "schema": "gunnchos.physical_pending_inventory.v1",
        "shipping_os": False,
        "physical_boot_claimed": False,
        "tokens": physical,
        "file_count": len({f for files in physical.values() for f in files}),
    }
    (out / "PHYSICAL_PENDING_INVENTORY.json").write_text(
        json.dumps(phys_payload, indent=2) + "\n", encoding="utf-8"
    )
    md_lines = [
        "# PHYSICAL_PENDING inventory",
        "",
        "Generated from source tokens. Digital work in this branch does **not**",
        "clear these items. Not a shipping OS. Not physical boot.",
        "",
    ]
    for token, files in physical.items():
        md_lines.append(f"## `{token}`")
        md_lines.append("")
        for f in files[:80]:
            md_lines.append(f"- `{f}`")
        if len(files) > 80:
            md_lines.append(f"- … {len(files) - 80} more")
        md_lines.append("")
    (ROOT / "docs" / "phd" / "PHYSICAL_PENDING.md").write_text(
        "\n".join(md_lines), encoding="utf-8"
    )
    return {"mocks": len(mocks), "physical_tokens": list(physical), "physical_files": phys_payload["file_count"]}


def main() -> int:
    summary = write_reports()
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
