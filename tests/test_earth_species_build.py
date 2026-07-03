"""Tests for Earth Species web build packaging."""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "games" / "earth-species-web"
DEST = ROOT / "apps" / "launcher_mock" / "public" / "games" / "earth-species-web"
BUILD = ROOT / "scripts" / "build_earth_species_web.sh"

FORBIDDEN_IP = ("Mario", "Kirby", "Sonic", "Pokemon", "Nintendo", "Pikachu")


def test_earth_species_source_files_exist():
    for name in ("index.html", "game.js", "style.css", "README.md"):
        assert (SRC / name).exists(), f"Missing {name}"


def test_build_script_runs():
    rc = subprocess.call(["bash", str(BUILD)], cwd=ROOT)
    assert rc == 0


def test_built_index_exists():
    subprocess.call(["bash", str(BUILD)], cwd=ROOT)
    assert (DEST / "index.html").exists()
    html = (DEST / "index.html").read_text(encoding="utf-8")
    assert "Earth Species" in html
    for term in FORBIDDEN_IP:
        assert term not in html


def test_readme_claims_vertical_slice():
    readme = (SRC / "README.md").read_text(encoding="utf-8")
    assert "vertical slice" in readme.lower()
    assert "not" in readme.lower()
