"""Lane A — filesystem contract + reproducible image build."""
from __future__ import annotations

import json
from pathlib import Path

from gunnchos_device_os.stage2.filesystem import (
    CONTRACT_DIRS,
    ensure_sysroot,
    verify_contract,
)
from gunnchos_device_os.stage2.image_build import build_image


def test_filesystem_contract(tmp_path: Path):
    # Use artifacts-style path under repo to satisfy guard when resolved
    root = Path("artifacts/stage2/test_sysroot_fs")
    if root.exists():
        import shutil

        shutil.rmtree(root)
    layout = ensure_sysroot(root)
    assert set(layout.created) == set(CONTRACT_DIRS)
    v = verify_contract(root)
    assert v["ok"] is True
    for name in CONTRACT_DIRS:
        assert (root / name).is_dir()


def test_image_build_artifacts_no_host_paths():
    repo = Path(__file__).resolve().parents[2]
    result = build_image(repo_root=repo)
    assert result["ok"] is True
    assert result["token"] == "OS_BASE_IMAGE_REAL"
    out = repo / "artifacts" / "stage2" / "image"
    required = [
        "system.img.tar",
        "recovery.img.tar",
        "MANIFEST.json",
        "packages.json",
        "sbom.cdx.json",
        "HASHES.json",
        "VERSION.json",
        "provenance.json",
    ]
    for name in required:
        assert (out / name).exists(), name
    manifest = json.loads((out / "MANIFEST.json").read_text())
    assert manifest["system_sha256"]
    assert manifest["signature"]
    for p in out.glob("*.json"):
        text = p.read_text()
        assert "/Users/" not in text, p.name
    # hashes match
    hashes = json.loads((out / "HASHES.json").read_text())
    assert hashes["system.img.tar"] == manifest["system_sha256"]
