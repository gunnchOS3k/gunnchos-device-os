"""LOCAL_SAVE_INTEGRITY_DIGITAL E4 prepared suite."""
from __future__ import annotations

from gunnchos_device_os.runtime.adapters import ContinuityService
from gunnchos_device_os.runtime.service_base import ServiceConfig
from gunnchos_device_os.security.wp007.game_save_integrity import (
    AUTHORITATIVE_MULTIPLAYER_INTEGRITY,
    run_digital_suite,
)


def test_local_save_integrity_digital_suite():
    suite = run_digital_suite()
    assert suite["passed"] is True
    assert suite["LOCAL_SAVE_INTEGRITY_DIGITAL"] == "E4_PREPARED"
    assert suite["AUTHORITATIVE_MULTIPLAYER_INTEGRITY"] == AUTHORITATIVE_MULTIPLAYER_INTEGRITY


def test_continuity_service_authenticated_save_and_tamper_reject():
    svc = ContinuityService(ServiceConfig(service_id="continuity", options={}))
    try:
        svc.on_start()
    except Exception:
        svc._store = {"saves": {}, "session_id": "dev"}
    saved = svc.api_save_state("slotA", {"level": 2, "score": 40})
    assert saved["authenticated"] is True
    assert saved["state"]["payload"]["mac"]
    # Direct tamper in store
    svc._store["saves"]["slotA"]["payload"]["score"] = 99999
    resumed = svc.api_resume("slotA")
    assert resumed["resumed"] is False
    assert resumed["integrity"]["reason"] == "tamper_detected"
