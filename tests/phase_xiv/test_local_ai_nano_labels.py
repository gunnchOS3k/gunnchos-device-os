"""SmolLM2-135M Q4_K_M 512-ctx is Nano/fallback only — never Local Fast/Pro."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from gunnchos_device_os.phase_xiv.local_ai import (
    NANO_CONTEXT_TOKENS,
    NANO_DISPLAY_LABEL,
    NANO_QUANT,
    ROLE_FAST,
    ROLE_NANO,
    ROLE_PRO,
    SMOLLM2_FILENAME,
    SMOLLM2_MODEL_ID,
    LocalAiRuntime,
    ModelRegistry,
    assert_honest_smollm2_label,
    invoke_gunnchai_tutor_local,
)

ROOT = Path(__file__).resolve().parents[2]


def _fake_repo_with_smollm2(tmp_path: Path) -> Path:
    repo = tmp_path / "gunnchos-device-os"
    (repo / "os_build" / "phase_xiv" / "local_ai").mkdir(parents=True)
    gguf_dir = tmp_path / "gunnchAI3k" / "models" / "local"
    gguf_dir.mkdir(parents=True)
    (gguf_dir / SMOLLM2_FILENAME).write_bytes(b"FAKE_SMOLLM2_NANO_WEIGHTS\n")
    return repo


def test_claiming_smollm2_as_local_fast_fails(tmp_path):
    fake = tmp_path / SMOLLM2_FILENAME
    fake.write_bytes(b"not-a-real-gguf")
    reg = ModelRegistry(tmp_path / "reg")
    with pytest.raises(ValueError, match="Nano/fallback"):
        reg.register(SMOLLM2_MODEL_ID, fake, tier="fast", runtime="llama_cpp", role=ROLE_FAST)


def test_claiming_smollm2_as_local_pro_fails(tmp_path):
    fake = tmp_path / SMOLLM2_FILENAME
    fake.write_bytes(b"not-a-real-gguf")
    reg = ModelRegistry(tmp_path / "reg")
    with pytest.raises(ValueError, match="Nano/fallback"):
        reg.register(SMOLLM2_MODEL_ID, fake, tier="pro", runtime="llama_cpp", role=ROLE_PRO)


def test_claiming_smollm2_as_small_legacy_label_fails(tmp_path):
    fake = tmp_path / SMOLLM2_FILENAME
    fake.write_bytes(b"not-a-real-gguf")
    reg = ModelRegistry(tmp_path / "reg")
    with pytest.raises(ValueError, match="Nano/fallback"):
        reg.register(SMOLLM2_MODEL_ID, fake, tier="small", runtime="llama_cpp")


def test_assert_honest_smollm2_label_rejects_fast_pro_display():
    with pytest.raises(ValueError, match="Nano/fallback"):
        assert_honest_smollm2_label(
            SMOLLM2_MODEL_ID,
            tier="nano",
            role=ROLE_NANO,
            display_label="Local Fast",
            is_nano_fallback_only=True,
        )
    with pytest.raises(ValueError, match="Nano/fallback"):
        assert_honest_smollm2_label(
            SMOLLM2_MODEL_ID,
            tier="nano",
            role=ROLE_NANO,
            display_label="Local Pro",
            is_nano_fallback_only=True,
        )


def test_smollm2_registers_as_nano_fallback_only(tmp_path):
    repo = _fake_repo_with_smollm2(tmp_path)
    reg = ModelRegistry(tmp_path / "reg")
    rt = LocalAiRuntime(reg, timeout_s=5)
    models = rt.ensure_default_models(repo, include_llama=True)
    assert SMOLLM2_MODEL_ID in models
    rec = reg.models[SMOLLM2_MODEL_ID]
    assert rec.tier == "nano"
    assert rec.role == ROLE_NANO
    assert rec.is_nano_fallback_only is True
    assert rec.context_tokens == NANO_CONTEXT_TOKENS == 512
    assert rec.quant == NANO_QUANT == "Q4_K_M"
    assert rec.display_label == NANO_DISPLAY_LABEL
    assert rec.tier not in {"fast", "pro", "small", "medium"}
    inv = rt.intelligence_inventory()
    assert inv["preferred_daily_tier"] == "nano_fallback"
    assert inv["preferred"] == SMOLLM2_MODEL_ID
    assert inv["fast"]["present"] is False
    assert inv["fast"]["open"] is True
    assert inv["pro"]["present"] is False
    assert inv["pro"]["open"] is True
    assert inv["GUNNCHAI_APP_PRODUCT_COMPLETE"] is False
    assert inv["HUMAN_E6"] is False
    assert inv["smollm2_is_full_intelligence_layer"] is False


def test_llama_enabled_does_not_promote_smollm2_to_daily_fast_or_pro(tmp_path):
    repo = _fake_repo_with_smollm2(tmp_path)
    reg = ModelRegistry(tmp_path / "reg")
    rt = LocalAiRuntime(reg, timeout_s=5)
    rt.ensure_default_models(repo, include_llama=True)
    rec = reg.models[SMOLLM2_MODEL_ID]
    assert rec.tier != "fast"
    assert rec.tier != "pro"
    assert rec.role not in {ROLE_FAST, ROLE_PRO}
    assert rt.preferred_daily_tier == "nano_fallback"
    payload = json.dumps(rt.intelligence_inventory())
    assert "Local Fast GGUF" in payload
    assert "Local Pro GGUF" in payload


def test_fast_weights_preferred_over_smollm2_nano(tmp_path):
    repo = _fake_repo_with_smollm2(tmp_path)
    fast = tmp_path / "gunnchAI3k" / "models" / "local" / "SmolLM-360M-Instruct-Q4_K_M.gguf"
    fast.write_bytes(b"FAKE_FAST_360M\n")
    reg = ModelRegistry(tmp_path / "reg")
    rt = LocalAiRuntime(reg, timeout_s=5)
    models = rt.ensure_default_models(repo, include_llama=True)
    assert "local-fast" in models
    assert SMOLLM2_MODEL_ID in models
    assert rt.preferred == "local-fast"
    assert rt.preferred_daily_tier == "fast"
    assert reg.models[SMOLLM2_MODEL_ID].is_nano_fallback_only is True
    assert reg.models["local-fast"].tier == "fast"


def test_gunnchai_tutor_local_path_stamps_nano_inventory(tmp_path):
    repo = _fake_repo_with_smollm2(tmp_path)
    # Copy micro artifact layout is created by ensure_default_models.
    out = invoke_gunnchai_tutor_local(
        repo,
        prompt="Explain OFDM at a high level",
        registry_root=tmp_path / "tutor_reg",
        include_llama=True,
    )
    assert out["ok"] is True
    assert out["GUNNCHAI_APP_PRODUCT_COMPLETE"] is False
    assert out["HUMAN_E6"] is False
    assert out["smollm2_labeled_as_fast_or_pro"] is False
    inv = out["intelligence"]
    assert inv["nano"]["is_nano_fallback_only"] is True
    assert inv["nano"]["context_tokens"] == 512
    assert inv["fast"]["open"] is True
    assert inv["pro"]["open"] is True
    # Without llama-cli the runtime falls back to micro, still not Fast/Pro.
    assert out["reply"]["tier"] in {"nano", "micro"}
    assert out["reply"]["tier"] not in {"fast", "pro", "small"}


def test_sdk_gunnchai_tutor_requires_first_party_import():
    text = (ROOT / "sdk" / "apps" / "gunnchai_tutor" / "main.py").read_text(encoding="utf-8")
    assert "from gunnchos_device_os.first_party_apps.gunnchai_tutor import run_gunnchai_tutor" in text
    assert "except ImportError" not in text
    assert "import invoke_gunnchai_tutor_local" not in text
    assert "invoke_gunnchai_tutor_local(" not in text
    manifest = json.loads(
        (ROOT / "sdk" / "apps" / "gunnchai_tutor" / "manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["version"] >= "0.3.0"
    assert manifest["source"] == "gunnchos_device_os.first_party_apps.gunnchai_tutor"
    assert manifest["platform001"] is True
    assert "ai_interface" in manifest["permissions"]
    assert "ai_interface.query" in manifest["capabilities_required"]
    assert "storage_read" in manifest["permissions"]
    assert "storage_write" in manifest["permissions"]


def test_sdk_gunnchai_tutor_entrypoint_invokes_local_ai(tmp_path, monkeypatch):
    import runpy

    monkeypatch.setenv("GUNNCHOS_REPO_ROOT", str(ROOT))
    monkeypatch.setenv("GUNNCHOS_SANDBOX_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("GUNNCHOS_APP_PERMISSIONS", "storage_read,storage_write,ai_interface")
    monkeypatch.setattr(
        "sys.argv",
        [str(ROOT / "sdk" / "apps" / "gunnchai_tutor" / "main.py")],
    )
    with pytest.raises(SystemExit) as exc:
        runpy.run_path(str(ROOT / "sdk" / "apps" / "gunnchai_tutor" / "main.py"), run_name="__main__")
    assert exc.value.code == 0
    payload = json.loads((tmp_path / "gunnchai_tutor_run.json").read_text(encoding="utf-8"))
    assert payload["ok"] is True
    assert payload["GUNNCHAI_APP_PRODUCT_COMPLETE"] is False
    assert payload["HUMAN_E6"] is False
    assert payload["tutor_entrypoint"] == "first_party_run_gunnchai_tutor"
    assert payload["persisted_session_count"] >= 1
    assert payload["intelligence"]["smollm2_is_full_intelligence_layer"] is False
    assert payload["intelligence"]["nano"]["is_nano_fallback_only"] is True
    assert payload["intelligence"]["nano_fallback_only"] is True
    assert payload["intelligence"]["owner_gunnchai_sha"]
    assert payload["intelligence"]["preferred_daily_tier"] in {"fast", "pro", "nano_fallback", "micro"}
    assert "weights_present" in payload["intelligence"]
