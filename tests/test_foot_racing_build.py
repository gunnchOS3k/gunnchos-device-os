"""Tests for Foot Racing web build packaging."""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "games" / "foot-racing-web"
DEST = ROOT / "apps" / "launcher_mock" / "public" / "games" / "foot-racing-web"
BUILD = ROOT / "scripts" / "build_foot_racing_web.sh"

FORBIDDEN_IP = ("Mario", "Kirby", "Sonic", "Pokemon", "Nintendo", "Smash")


def test_foot_racing_source_files_exist():
    for name in ("index.html", "game.js", "style.css", "README.md"):
        assert (SRC / name).exists(), f"Missing {name}"


def test_build_script_runs():
    rc = subprocess.call(["bash", str(BUILD)], cwd=ROOT)
    assert rc == 0


def test_built_index_exists():
    subprocess.call(["bash", str(BUILD)], cwd=ROOT)
    assert (DEST / "index.html").exists()
    html = (DEST / "index.html").read_text(encoding="utf-8")
    assert "Foot Racing" in html
    for term in FORBIDDEN_IP:
        assert term not in html


def test_readme_claims_vertical_slice():
    readme = (SRC / "README.md").read_text(encoding="utf-8")
    assert "vertical slice" in readme.lower()
    assert "not" in readme.lower()
