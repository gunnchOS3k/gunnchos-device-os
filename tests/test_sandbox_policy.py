"""Sandbox policy engine — isolation model tests."""
from __future__ import annotations

import pytest

from gunnchos_device_os.sandbox_policy import (
    Capability,
    Decision,
    IsolationLevel,
    SandboxPolicyEngine,
)


def test_third_party_defaults_to_process_isolation():
    eng = SandboxPolicyEngine()
    p = eng.create_profile("notes", "third_party")
    assert p.isolation == IsolationLevel.PROCESS
    assert Capability.NET_CONNECT in p.granted
    assert Capability.SYSTEM_SERVICE in p.dropped
    assert eng.check_capability("notes", Capability.SYSTEM_SERVICE)["decision"] == Decision.DENY.value


def test_untrusted_is_strict_and_net_denied():
    eng = SandboxPolicyEngine()
    p = eng.create_profile("sideload", "untrusted")
    assert p.isolation == IsolationLevel.STRICT
    assert p.net_policy == "deny"
    assert eng.check_capability("sideload", Capability.NET_CONNECT)["decision"] == Decision.DENY.value


def test_strict_rejects_extra_caps():
    eng = SandboxPolicyEngine()
    with pytest.raises(PermissionError):
        eng.create_profile(
            "x",
            "untrusted",
            extra_caps={Capability.NET_CONNECT},
        )


def test_first_party_can_use_gpu():
    eng = SandboxPolicyEngine()
    eng.create_profile("game", "game")
    assert eng.check_capability("game", Capability.DEVICE_GPU)["decision"] == Decision.ALLOW.value


def test_ipc_requires_peer_allowlist():
    eng = SandboxPolicyEngine()
    eng.create_profile("a", "third_party", ipc_peers=["b"])
    eng.create_profile("b", "third_party")
    assert eng.may_ipc("a", "b")["decision"] == Decision.ALLOW.value
    assert eng.may_ipc("b", "a")["decision"] == Decision.DENY.value


def test_system_may_ipc_freely():
    eng = SandboxPolicyEngine()
    eng.create_profile("sys", "system")
    eng.create_profile("app", "first_party")
    assert eng.may_ipc("sys", "app")["decision"] == Decision.ALLOW.value


def test_isolate_process_namespaces_differ_by_level():
    eng = SandboxPolicyEngine()
    eng.create_profile("browser", "browser")
    rec = eng.isolate_process("browser", "renderer")
    assert "renderer" in rec["namespace"]
    assert rec["mock"] is False
    eng.create_profile("shell", "first_party")
    rec2 = eng.isolate_process("shell", "main")
    assert "main" not in rec2["namespace"]  # app-level shares ns


def test_assert_capability_raises():
    eng = SandboxPolicyEngine()
    eng.create_profile("x", "untrusted")
    with pytest.raises(PermissionError):
        eng.assert_capability("x", Capability.DEVICE_CAMERA)


def test_escalation_requires_approver():
    eng = SandboxPolicyEngine()
    eng.create_profile("lab", "third_party")
    denied = eng.escalate("lab", Capability.DEVICE_MIC)
    assert denied["decision"] == Decision.DENY.value
    allowed = eng.escalate("lab", Capability.DEVICE_MIC, approved_by="guardian")
    assert allowed["decision"] == Decision.ALLOW.value
    eng.assert_capability("lab", Capability.DEVICE_MIC)


def test_strict_blocks_dangerous_escalation():
    eng = SandboxPolicyEngine()
    eng.create_profile("malware", "untrusted")
    r = eng.escalate("malware", Capability.SYSTEM_SERVICE, approved_by="admin")
    assert r["decision"] == Decision.DENY.value
    assert r["reason"] == "strict_blocks_dangerous_escalation"


def test_unknown_app_class_raises():
    eng = SandboxPolicyEngine()
    with pytest.raises(ValueError):
        eng.create_profile("x", "quantum")


def test_status_not_mock():
    eng = SandboxPolicyEngine()
    eng.create_profile("a", "first_party")
    st = eng.status()
    assert st["mock"] is False
    assert "a" in st["profiles"]
    assert "claim_boundary" in st
