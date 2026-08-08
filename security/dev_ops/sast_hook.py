#!/usr/bin/env python3
"""Lightweight SAST hook for DEV plane — no external scanner required.

Scans Python sources for high-risk patterns: hardcoded production secrets,
eval/exec, pickle.loads, disable-ssl, PROD enrollment tokens.
Exit 1 on findings (for CI/pre-commit). DEV_ tokens and test fixtures allowed.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCAN_ROOTS = [
    ROOT / "gunnchos_device_os" / "cloud_dev_plane",
    ROOT / "gunnchos_device_os" / "cloud_edge",
    ROOT / "gunnchos_device_os" / "fleet_ops.py",
    ROOT / "deploy" / "cloud_dev_plane",
]

FORBIDDEN_SUBSTRINGS = [
    (re.compile(r"BEGIN RSA PRIVATE KEY"), "pem_private_key"),
    (re.compile(r"(?i)AKIA[0-9A-Z]{16}"), "aws_access_key_pattern"),
    (re.compile(r"(?i)password\\s*=\\s*[\"'](?!DEV_|test_|dummy_|\\[REDACTED\\])[^\"']+[\"']"), "hardcoded_password"),
    (re.compile(r"(?i)enrollment_token\\s*=\\s*[\"'](?!DEV_)[^\"']+[\"']"), "non_dev_enrollment_token"),
    (re.compile(r"verify\\s*=\\s*False"), "ssl_verify_disabled"),
]

AST_BANNED = {"eval", "exec", "compile"}


def iter_py_files() -> list[Path]:
    files: list[Path] = []
    for root in SCAN_ROOTS:
        if root.is_file() and root.suffix == ".py":
            files.append(root)
        elif root.is_dir():
            files.extend(root.rglob("*.py"))
    return sorted(set(files))


def scan_file(path: Path) -> list[dict]:
    findings: list[dict] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    rel = str(path.relative_to(ROOT))
    for pattern, code in FORBIDDEN_SUBSTRINGS:
        for i, line in enumerate(text.splitlines(), 1):
            if pattern.search(line):
                findings.append({"file": rel, "line": i, "code": code, "snippet": line.strip()[:120]})
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        findings.append({"file": rel, "line": exc.lineno or 0, "code": "syntax_error", "snippet": str(exc)})
        return findings
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in AST_BANNED:
            findings.append(
                {
                    "file": rel,
                    "line": getattr(node, "lineno", 0),
                    "code": f"banned_call_{node.func.id}",
                    "snippet": node.func.id,
                }
            )
        if isinstance(node, ast.Attribute) and node.attr == "loads":
            # pickle.loads
            if isinstance(node.value, ast.Name) and node.value.id == "pickle":
                findings.append(
                    {
                        "file": rel,
                        "line": getattr(node, "lineno", 0),
                        "code": "pickle_loads",
                        "snippet": "pickle.loads",
                    }
                )
    return findings


def main() -> int:
    findings: list[dict] = []
    for path in iter_py_files():
        findings.extend(scan_file(path))
    if findings:
        print(f"SAST_HOOK_FAIL count={len(findings)}")
        for f in findings:
            print(f"  {f['file']}:{f['line']} [{f['code']}] {f['snippet']}")
        return 1
    print("SAST_HOOK_OK realm=DEV scanned=%d" % len(iter_py_files()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
