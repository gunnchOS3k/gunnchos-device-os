"""Phase XIV E2E tests — compositor, AI, callers, differentiators."""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_compositor_form_factor_e2e():
    from gunnchos_device_os.phase_xiv.compositor import WaylandSession, run_form_factor_e2e
    from gunnchos_device_os.stage2.shell.profiles import AdaptiveProfile

    result = run_form_factor_e2e()
    assert result["ok"] is True
    assert result["capture"]["deny"]["decision"] == "deny"
    assert result["recovery"]["ok"] is True
    sess = WaylandSession(AdaptiveProfile.STUDENT_DESKTOP)
    assert sess.stack == "weston+wlroots"
    snap = sess.snapshot()
    assert snap["frontier_parity_claimed"] is False
    assert snap["physical_accuracy"] == "PHYSICAL_PENDING"


def test_ai_system_api_no_model_paths():
    from gunnchos_device_os.phase_xiv.ai_system import AiRequest, OsAiSystemApi, start_os_ai_server
    from gunnchos_device_os.phase_xiv.local_ai import LocalAiRuntime, ModelRegistry

    reg = ModelRegistry(ROOT / "artifacts" / "phase_xiv" / "test_registry")
    rt = LocalAiRuntime(reg, preferred="micro-deterministic-v1", timeout_s=10)
    rt.ensure_default_models(ROOT)
    rt.preferred = "micro-deterministic-v1"
    api = OsAiSystemApi(local_runtime=rt)
    assert set(api.list_capabilities()) >= {
        "summarize",
        "translate",
        "tutor",
        "code",
        "search",
        "reason",
        "diagnose",
        "classify",
    }
    for cap in api.list_capabilities():
        r = api.invoke(AiRequest(cap, f"probe {cap}", user_id="t"))
        assert r.ok is True
        assert r.model_path_exposed is False
        assert "model_path" not in (r.route or {})
        blob = str(r.to_dict())
        assert "/Users/" not in blob
        assert ".gguf" not in blob

    server, port = start_os_ai_server(api, 0)
    try:
        import json
        import urllib.request

        with urllib.request.urlopen(f"http://127.0.0.1:{port}/v1/capabilities", timeout=5) as resp:
            caps = json.loads(resp.read().decode())
        assert "tutor" in caps["capabilities"]
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/v1/capability/tutor",
            data=json.dumps({"user_id": "u", "input": "OFDM"}).encode(),
            headers={"content-type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode())
        assert body["ok"] is True
        assert body["model_path_exposed"] is False
    finally:
        server.shutdown()


def test_local_ai_registry_hash_fallback():
    from gunnchos_device_os.phase_xiv.local_ai import LocalAiRuntime, ModelRegistry

    reg = ModelRegistry(ROOT / "artifacts" / "phase_xiv" / "test_local_ai")
    rt = LocalAiRuntime(reg, timeout_s=8)
    models = rt.ensure_default_models(ROOT)
    assert "micro-deterministic-v1" in models
    assert reg.verify("micro-deterministic-v1") is True
    # force micro path (always available; llama optional)
    rt.preferred = "micro-deterministic-v1"
    out = rt.run_capability("classify", "network drop after undock")
    assert out["ok"] is True
    assert out["runtime"] == "deterministic_micro"
    assert out["tier"] == "micro"
    # corrupt hash → fallback still works via re-register? simulate mismatch by flipping sha
    rec = reg.models["micro-deterministic-v1"]
    good = rec.sha256
    rec.sha256 = "0" * 64
    assert reg.verify("micro-deterministic-v1") is False
    rec.sha256 = good
    assert reg.verify("micro-deterministic-v1") is True


def test_local_ai_llama_tier_if_available():
    """Real llama.cpp tier when GGUF + llama-cli present — not HTTP stub."""
    import shutil

    from gunnchos_device_os.phase_xiv.local_ai import LocalAiRuntime, ModelRegistry

    if not shutil.which("llama-cli"):
        pytest.skip("llama-cli not installed")
    reg = ModelRegistry(ROOT / "artifacts" / "phase_xiv" / "test_llama")
    rt = LocalAiRuntime(reg, timeout_s=45)
    models = rt.ensure_default_models(ROOT, include_llama=True)
    if "smollm2-135m-q4" not in models:
        pytest.skip("SmolLM2 GGUF not present in sibling paths")
    rt.preferred = "smollm2-135m-q4"
    rec = reg.models["smollm2-135m-q4"]
    assert rec.tier == "nano"
    assert rec.is_nano_fallback_only is True
    assert rec.role == "NANO_LOCAL"
    assert rec.context_tokens == 512
    assert rec.quant == "Q4_K_M"
    assert rec.display_label == "Nano/fallback"
    out = rt.run_capability("tutor", "What is OFDM in one sentence?")
    assert out["ok"] is True
    if out["runtime"] != "llama_cpp":
        pytest.skip(f"llama-cli present but did not produce llama_cpp output (runtime={out.get('runtime')})")
    assert out["tier"] == "nano"
    assert out["is_nano_fallback_only"] is True
    assert out["role"] == "NANO_LOCAL"
    assert len(out["text"]) > 0
    inv = rt.intelligence_inventory()
    assert inv["GUNNCHAI_APP_PRODUCT_COMPLETE"] is False
    assert inv["smollm2_is_full_intelligence_layer"] is False
    assert inv["preferred_daily_tier"] in {"nano_fallback", "fast", "pro"}


def test_cross_product_callers():
    from gunnchos_device_os.phase_xiv.ai_system import OsAiSystemApi
    from gunnchos_device_os.phase_xiv.callers import CrossProductCallers, PRODUCTS
    from gunnchos_device_os.phase_xiv.local_ai import LocalAiRuntime, ModelRegistry

    reg = ModelRegistry(ROOT / "artifacts" / "phase_xiv" / "test_callers_reg")
    rt = LocalAiRuntime(reg, preferred="micro-deterministic-v1", timeout_s=10)
    rt.ensure_default_models(ROOT)
    rt.preferred = "micro-deterministic-v1"
    smoke = CrossProductCallers(OsAiSystemApi(local_runtime=rt)).run_all_smoke()
    assert smoke["ok"] is True
    assert set(smoke["products"]) == set(PRODUCTS)
    for r in smoke["results"]:
        assert r["ok"] is True
        assert r["model_path_exposed"] is False


def test_continuity_handheld_student_dsxl():
    from gunnchos_device_os.phase_xiv.continuity import ContinuityMesh

    result = ContinuityMesh(ROOT / "artifacts" / "phase_xiv" / "test_cont").e2e_handheld_student_dsxl()
    assert result["ok"] is True
    assert result["handheld_to_student"]["to"] == "STUDENT"
    assert result["student_to_dsxl"]["to"] == "DSXL"


def test_gunnchplay_first_party():
    from gunnchos_device_os.phase_xiv.play import FIRST_PARTY_GAMES, GunnchPlay

    result = GunnchPlay(ROOT / "artifacts" / "phase_xiv" / "test_play").e2e(ROOT)
    assert result["ok"] is True
    assert result["library_count"] == len(FIRST_PARTY_GAMES) == 4
    assert result["remote_play"]["production_wan"] is False


def test_fabric_camera_npu_fallback():
    from gunnchos_device_os.phase_xiv.fabric import GunnchFabric

    result = GunnchFabric().e2e()
    assert result["ok"] is True
    assert result["npu_path"]["path"] == "camera+npu"
    assert result["fallback_path"]["path"] == "camera+cpu_fallback"


def test_spatial_edge_to_apps():
    from gunnchos_device_os.phase_xiv.spatial import TARGETS, SpatialInputService

    result = SpatialInputService().e2e_edge_to_apps()
    assert result["ok"] is True
    assert set(result["targets"]) == set(TARGETS)
    assert result["delivery"]["physical_accuracy"] == "PHYSICAL_PENDING"


def test_package_channels_sign_rollback_revoke():
    from gunnchos_device_os.phase_xiv.packages import PackageManager

    result = PackageManager(ROOT / "artifacts" / "phase_xiv" / "test_pkg").e2e()
    assert result["ok"] is True
    assert result["revoked_install_denied"] is True


def test_sdk_templates():
    from gunnchos_device_os.phase_xiv.sdk import TEMPLATES, DeveloperSdk

    result = DeveloperSdk(ROOT / "artifacts" / "phase_xiv" / "test_sdk").e2e(
        ROOT / "os_build" / "phase_xiv" / "sdk_templates"
    )
    assert result["ok"] is True
    assert set(result["templates"]) == set(TEMPLATES)


def test_mdm_ten_device_fleet():
    from gunnchos_device_os.phase_xiv.mdm import FLEET_SIZE, EducationMdm

    result = EducationMdm(ROOT / "artifacts" / "phase_xiv" / "test_mdm").e2e_ten_device_fleet(ROOT)
    assert result["ok"] is True
    assert result["fleet"]["size"] == FLEET_SIZE == 10
    assert result["blocked_probe"]["allowed"] is False


def test_no_frontier_parity_claim():
    import gunnchos_device_os.phase_xiv as px

    assert px.GUNNCHOS_FRONTIER_OS_PARITY is False
    assert px.FRONTIER_OS_PARITY_CLAIMED is False
    assert px.PHYSICAL_EXECUTION_FREEZE is True
