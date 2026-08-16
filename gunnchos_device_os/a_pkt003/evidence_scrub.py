"""Scrub host absolute paths / machine identity from A-PKT-003 evidence JSON."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

_ABS_USER = re.compile(r"/Users/[^/\s\"']+(?:/[^\"'\s]*)?")
_VAR_FOLDERS = re.compile(r"/var/folders/[^\"'\s]+")
_TMP_CURSOR = re.compile(r"/tmp/[^\"'\s]+")
_HOSTNAME_LOCAL = re.compile(r"\b[\w.-]+\.local\b")


def relpath_or_redact(path: Path | str, repo_root: Path) -> str:
    """Return repo-relative path when under repo; otherwise a redacted token."""
    p = Path(path)
    try:
        return p.resolve().relative_to(repo_root.resolve()).as_posix()
    except (ValueError, OSError):
        name = p.name or "path"
        return f"<redacted>/{name}"


def scrub_string(text: str, repo_root: Path) -> str:
    root = repo_root.resolve().as_posix()
    if text.startswith(root + "/") or text == root:
        return relpath_or_redact(text, repo_root)
    # Also handle worktree / alternate checkout absolutes that share the repo name.
    text = _ABS_USER.sub(lambda m: _user_path_redact(m.group(0), repo_root), text)
    text = _VAR_FOLDERS.sub("<tmpdir>/playwright-or-cache", text)
    text = _TMP_CURSOR.sub("<tmpdir>", text)
    text = _HOSTNAME_LOCAL.sub("<lab-host>", text)
    return text


def _user_path_redact(abs_path: str, repo_root: Path) -> str:
    marker = "/repos/"
    if marker in abs_path:
        # Prefer artifacts/... or path after repo directory name when recognizable.
        parts = abs_path.split("/")
        for i, part in enumerate(parts):
            if part.startswith("gunnchos-device-os") and i + 1 < len(parts):
                return "/".join(parts[i + 1 :]) or "<redacted>"
        return "<redacted>/host-path"
    try:
        return relpath_or_redact(abs_path, repo_root)
    except Exception:  # noqa: BLE001
        return "<redacted>/host-path"


def scrub_obj(obj: Any, repo_root: Path) -> Any:
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for k, v in obj.items():
            if k in {"host", "hostname"} and isinstance(v, str):
                out[k] = "<lab-host>"
            else:
                out[k] = scrub_obj(v, repo_root)
        return out
    if isinstance(obj, list):
        return [scrub_obj(x, repo_root) for x in obj]
    if isinstance(obj, Path):
        return relpath_or_redact(obj, repo_root)
    if isinstance(obj, str):
        return scrub_string(obj, repo_root)
    return obj


def write_scrubbed_json(path: Path, doc: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    cleaned = scrub_obj(doc, repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cleaned, indent=2, default=str) + "\n", encoding="utf-8")
    return cleaned


def scrub_artifact_tree(artifact_dir: Path, repo_root: Path) -> list[str]:
    """Rewrite all *.json under artifact_dir in place; return touched relative paths."""
    touched: list[str] = []
    if not artifact_dir.is_dir():
        return touched
    for path in sorted(artifact_dir.rglob("*.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        cleaned = scrub_obj(raw, repo_root)
        if cleaned != raw:
            path.write_text(json.dumps(cleaned, indent=2, default=str) + "\n", encoding="utf-8")
            touched.append(relpath_or_redact(path, repo_root))
    return touched
