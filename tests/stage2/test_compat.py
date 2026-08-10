"""Lane C — compatibility registry, classifier, corpus honesty."""
from __future__ import annotations

from gunnchos_device_os.stage2.compat.classifier import CompatClass, classify
from gunnchos_device_os.stage2.compat.corpus import run_corpus
from gunnchos_device_os.stage2.compat.proton import run_redistributable_test_app, STEAM_USER_EXTERNAL
from gunnchos_device_os.stage2.compat.registry import CompatRegistry, RuntimeLane


def test_registry_lanes_and_android_default():
    reg = CompatRegistry()
    lanes = {RuntimeLane(x["lane"]) for x in reg.list_lanes()}
    assert lanes == set(RuntimeLane)
    android = reg.get(RuntimeLane.ANDROID_EXPERIMENTAL)
    assert android.evaluated is False
    assert android.enabled is False


def test_classifier_unknown_when_absent():
    r = classify({"binary_present": False, "skipped": True, "skip_reason": "missing"})
    assert r["class"] == CompatClass.UNKNOWN.value


def test_corpus_never_fakes_pass():
    report = run_corpus()
    assert report["fake_pass_detected"] is False
    assert report["ok"] is True
    # terminal/git should usually be present on CI/dev hosts
    by_id = {r["id"]: r for r in report["results"]}
    assert by_id["terminal"]["class"] in {
        CompatClass.VERIFIED.value,
        CompatClass.NATIVE.value,
        CompatClass.PLAYABLE.value,
    }
    for r in report["results"]:
        if r["class"] in (
            CompatClass.VERIFIED.value,
            CompatClass.NATIVE.value,
            CompatClass.PLAYABLE.value,
        ):
            assert r["binary"], f"fake pass for {r['id']}"


def test_proton_steam_user_external_unknown_without_fixture():
    assert STEAM_USER_EXTERNAL is True
    r = run_redistributable_test_app(None)
    assert r["class"] == CompatClass.UNKNOWN.value
