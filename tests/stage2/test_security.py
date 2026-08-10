"""Lane D — trust, sandbox denials, mode escalation logged/reversible."""
from __future__ import annotations

import shutil
from pathlib import Path

from gunnchos_device_os.stage2.crypto_dev import sign_payload
from gunnchos_device_os.stage2.security.modes import ModeManager, SecurityMode
from gunnchos_device_os.stage2.security.sandbox import (
    Permission,
    SandboxEnforcer,
    SandboxProfile,
)
from gunnchos_device_os.stage2.security.trust import TrustChain


def _dir() -> Path:
    p = Path("artifacts/stage2/test_security")
    if p.exists():
        shutil.rmtree(p)
    p.mkdir(parents=True)
    return p


def test_denial_and_revocation():
    root = _dir()
    enf = SandboxEnforcer(root)
    enf.set_profile(
        SandboxProfile(
            "app.x",
            allow={Permission.NET, Permission.FS_HOME},
            deny={Permission.FS_SYSTEM},
        )
    )
    d = enf.check("app.x", Permission.FS_SYSTEM)
    assert d["decision"] == "deny"
    enf.revoke("app.x", Permission.NET)
    d2 = enf.check("app.x", Permission.NET)
    assert d2["decision"] == "deny"
    assert enf.denials_path.exists()


def test_per_user_isolation_and_secrets():
    root = _dir()
    enf = SandboxEnforcer(root)
    a = enf.isolate_user("alice")
    b = enf.isolate_user("bob")
    assert a != b
    enf.secret_put("alice", "k", "v")
    assert enf.secret_get("alice", "k") == "v"
    assert enf.secret_get("bob", "k") is None


def test_developer_escalation_logged_and_reversible():
    root = _dir()
    modes = ModeManager(root / "modes")
    assert modes.current() == SecurityMode.CONSUMER
    esc = modes.escalate(SecurityMode.DEVELOPER, reason="unit-test")
    assert esc["ok"] and esc["logged"]
    assert modes.current() == SecurityMode.DEVELOPER
    rev = modes.revert()
    assert rev["ok"] and rev["reversible"]
    assert modes.current() == SecurityMode.CONSUMER
    log = modes.audit_log()
    assert any(e["event"] == "escalate" for e in log)
    assert any(e["event"] == "revert" for e in log)


def test_anti_rollback_and_app_signature():
    root = _dir()
    trust = TrustChain(root / "trust")
    trust.set_security_version(3)
    meta = {
        "schema": "upd",
        "security_version": 2,
        "realm": "gunnchos-stage2-dev-signing-v1",
        "artifact_sha256": "a" * 64,
    }
    meta["signature"] = sign_payload(meta)
    assert trust.verify_update_metadata(meta)["reason"] == "anti_rollback"
    app = b"hello-app"
    sig = trust.sign_app(app, "com.example")
    assert trust.verify_app_signature(app, sig)["ok"] is True
    assert trust.verify_app_signature(b"tampered", sig)["ok"] is False
