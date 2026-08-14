"""Unit tests for WAIKE owner package ingest (no curriculum re-author)."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from gunnchos_device_os.product_use.waike_owner_package import WaikeOwnerPackageStore

REPO = Path(__file__).resolve().parents[2]
OWNER = REPO.parent / "waike-research-ops"


@pytest.fixture()
def store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> WaikeOwnerPackageStore:
    # Isolate store + signing keys under tmp.
    root = tmp_path / "device-os"
    (root / "gunnchos_device_os").mkdir(parents=True)
    monkeypatch.chdir(root)
    return WaikeOwnerPackageStore(root)


@pytest.mark.skipif(not (OWNER / "ingest/learner/waike_learner_ingest.v1.json").exists(), reason="owner ingest missing")
def test_import_owner_signed_learner_teacher_and_rollback(store: WaikeOwnerPackageStore) -> None:
    first = store.import_owner(OWNER, owner_commit="test-commit", package_version="v-test-a")
    assert first["ok"] is True
    assert first["signature_ok"] is True
    assert first["reauthored_in_device_os"] is False
    assert set(first["course_ids"]) == {"GENERAL_IT", "COMPUTER_NETWORKING", "CYBERSECURITY"}

    learner = store.view("learner")
    teacher = store.view("teacher")
    assert learner["ok"] and teacher["ok"]
    learner_blob = json.dumps(learner["doc"])
    teacher_blob = json.dumps(teacher["doc"])
    assert "answer_keys" not in learner_blob
    assert "answer_index" not in learner_blob
    assert "instructor_notes" not in learner_blob
    assert "answer_keys" in teacher_blob

    second = store.import_owner(OWNER, owner_commit="test-commit-2", package_version="v-test-b")
    assert second["ok"] is True
    assert store._load_index()["active_version"] == "v-test-b"

    rolled = store.rollback("v-test-a")
    assert rolled["ok"] is True
    assert store._load_index()["active_version"] == "v-test-a"
    assert store._load_index()["last_migration"]["kind"] == "rollback"
    assert store.verify_version("v-test-a") is True


@pytest.mark.skipif(not (OWNER / "ingest/learner/waike_learner_ingest.v1.json").exists(), reason="owner ingest missing")
def test_import_does_not_copy_owner_tree_into_module_source(store: WaikeOwnerPackageStore) -> None:
    store.import_owner(OWNER, package_version="v-nocopy")
    # Curriculum modules must remain absent from product_use source.
    product_use = REPO / "gunnchos_device_os" / "product_use"
    for name in ("GENERAL_IT", "COMPUTER_NETWORKING", "CYBERSECURITY", "lesson.md"):
        assert not any(product_use.rglob(name)), f"unexpected curriculum path {name}"
