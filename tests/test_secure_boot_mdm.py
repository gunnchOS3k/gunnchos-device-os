"""Phase 4D secure boot and MDM architecture tests."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
KEY_DIR = ROOT / "security" / "secure_boot" / "dev_keys"
PRIV = KEY_DIR / "image_signing_dev.pem"
PUB = KEY_DIR / "image_signing_dev.pub.pem"
MANIFEST = ROOT / "release_artifacts" / "version_manifest.example.json"
SIGNED = ROOT / "release_artifacts" / "version_manifest.example.signed.json"
SAMPLE_POLICY = ROOT / "mdm" / "sample_policies" / "school_default.json"


@pytest.fixture(scope="module", autouse=True)
def dev_keys() -> None:
    if not PRIV.exists():
        rc = subprocess.call(["bash", str(ROOT / "scripts" / "generate_dev_signing_keys.sh")], cwd=ROOT)
        assert rc == 0


def test_secure_boot_docs_exist():
    for path in (
        ROOT / "security/secure_boot/ARCHITECTURE.md",
        ROOT / "security/secure_boot/CLAIM_BOUNDARY.md",
        ROOT / "security/secure_boot/SECURE_BOOT_CHECKLIST.md",
        ROOT / "docs/PHASE4D_SECURE_BOOT_MDM.md",
    ):
        assert path.exists(), f"missing {path}"


def test_mdm_docs_and_schema_exist():
    assert (ROOT / "mdm/policy_schema.yaml").exists()
    assert (ROOT / "mdm/CLAIM_BOUNDARY.md").exists()
    assert (ROOT / "mdm/enrollment_profile.example.json").exists()
    assert (ROOT / "mdm/device_policy_agent.py").exists()


def test_sample_policies_load():
    from mdm.device_policy_agent import load_policy, evaluate_app

    for name in ("school_default.json", "library_session.json", "guardian_home.json"):
        policy = load_policy(ROOT / "mdm" / "sample_policies" / name)
        assert policy.deployment_mode in {"School", "Library", "Guardian"}
        blocked = evaluate_app(policy, "chatgpt")
        assert blocked.allowed is False


def test_device_policy_agent_cli():
    rc = subprocess.call(
        ["python3", str(ROOT / "mdm/device_policy_agent.py"), str(SAMPLE_POLICY), "notes"],
        cwd=ROOT,
    )
    assert rc == 0


def test_release_manifest_sign_and_verify():
    sign = subprocess.run(
        ["python3", str(ROOT / "scripts/sign_release_manifest.py"), str(MANIFEST), "-o", str(SIGNED)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert sign.returncode == 0, sign.stderr
    assert SIGNED.exists()

    verify = subprocess.run(
        ["python3", str(ROOT / "scripts/verify_release_manifest.py"), str(SIGNED)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert verify.returncode == 0, verify.stderr


def test_invalid_signature_fails():
    sign = subprocess.run(
        ["python3", str(ROOT / "scripts/sign_release_manifest.py"), str(MANIFEST), "-o", str(SIGNED)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert sign.returncode == 0
    data = json.loads(SIGNED.read_text(encoding="utf-8"))
    sig = data["signing"]["signature_b64"]
    data["signing"]["signature_b64"] = sig[:-4] + "AAAA"
    tampered = ROOT / "release_artifacts" / "version_manifest.example.tampered.json"
    tampered.write_text(json.dumps(data, indent=2), encoding="utf-8")

    verify = subprocess.run(
        ["python3", str(ROOT / "scripts/verify_release_manifest.py"), str(tampered)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert verify.returncode != 0
    tampered.unlink(missing_ok=True)


def test_beta_gate_blocks_production_mdm_and_secure_boot_validated():
    import yaml

    data = yaml.safe_load((ROOT / "beta_gate" / "beta_gate_status.yaml").read_text(encoding="utf-8"))
    mdm = data["items"].get("production_mdm", {})
    sb = data["items"].get("secure_boot", {})
    assert mdm.get("status") == "prototype"
    assert sb.get("status") == "prototype"
    assert data["beta_ready"] is False
