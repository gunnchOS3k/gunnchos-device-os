"""Path → Golden Journey subset selection for major PRs."""

from __future__ import annotations

import fnmatch
import json
from pathlib import Path
from typing import Any, Iterable


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_path_map(root: Path | None = None) -> dict[str, Any]:
    root = root or _root()
    return json.loads(
        (root / "quality/golden_journeys/PATH_TO_JOURNEY_MAP.json").read_text(encoding="utf-8")
    )


def load_catalog(root: Path | None = None) -> dict[str, Any]:
    root = root or _root()
    return json.loads(
        (root / "quality/golden_journeys/GOLDEN_JOURNEYS.json").read_text(encoding="utf-8")
    )


def _match(path: str, pattern: str) -> bool:
    # Support ** globs used in PATH_TO_JOURNEY_MAP
    if "**" in pattern:
        # Convert simple ** globs to fnmatch-friendly forms
        parts = pattern.split("**/")
        if len(parts) == 2 and parts[0] == "":
            return fnmatch.fnmatch(path, parts[1]) or f"/{parts[1]}" in f"/{path}"
        # prefix**/rest
        prefix, rest = pattern.split("**/", 1)
        if prefix and not path.startswith(prefix.rstrip("/")) and not path.startswith(prefix):
            # also allow exact directory prefix without trailing content
            if not path.startswith(prefix.rstrip("*").rstrip("/")):
                return fnmatch.fnmatch(path, pattern.replace("**/", ""))
        return fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(path, pattern.replace("**/", ""))
    return fnmatch.fnmatch(path, pattern)


def path_matches(path: str, globs: Iterable[str]) -> bool:
    norm = path.lstrip("./")
    for g in globs:
        gnorm = g.lstrip("./")
        if fnmatch.fnmatch(norm, gnorm):
            return True
        # directory prefix: foo/bar/** matches foo/bar/baz
        if gnorm.endswith("/**"):
            prefix = gnorm[:-3]
            if norm == prefix.rstrip("/") or norm.startswith(prefix):
                return True
        # trailing dir without glob
        if gnorm.endswith("/") and norm.startswith(gnorm):
            return True
    return False


def select_journeys_for_paths(
    changed_paths: Iterable[str],
    *,
    root: Path | None = None,
    force_all: bool = False,
    major_pr: bool = True,
) -> dict[str, Any]:
    """Select Golden Journey IDs relevant to changed paths.

    On major PRs with no matching paths, defaults to S0 journeys (GOLDEN-09/10).
    """
    root = root or _root()
    path_map = load_path_map(root)
    catalog = load_catalog(root)
    paths = [p.lstrip("./") for p in changed_paths]

    if force_all:
        selected = [j["id"] for j in catalog["journeys"]]
        reason = "force_all"
    else:
        selected = []
        for jid, entry in path_map["journeys"].items():
            if any(path_matches(p, entry.get("path_globs", [])) for p in paths):
                selected.append(jid)
        selected = sorted(set(selected), key=lambda x: int(x.split("-")[1]))
        reason = "path_match"
        if major_pr and not selected:
            selected = list(path_map.get("default_on_unknown_major", ["GOLDEN-09", "GOLDEN-10"]))
            reason = "major_pr_default_s0"

    severities = {j["id"]: j["severity"] for j in catalog["journeys"]}
    return {
        "schema": "gunnchos.golden_journey_subset.v1",
        "selected": selected,
        "reason": reason,
        "severities": {jid: severities[jid] for jid in selected},
        "changed_paths": paths,
        "major_pr": major_pr,
        "independent_verification_claimed": False,
    }
