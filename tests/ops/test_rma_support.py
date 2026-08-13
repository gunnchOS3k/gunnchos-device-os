from __future__ import annotations

import json
from pathlib import Path

from gunnchos_device_os.ops.fault_codes import list_codes, lookup
from gunnchos_device_os.ops.rma import RmaSupportDesk
from gunnchos_device_os.ops.spares import UNKNOWN, map_spares

REPO_ROOT = Path(__file__).resolve().parents[2]


def _device_root(tmp_path, name="device"):
    root = tmp_path / name
    (root / "logs").mkdir(parents=True)
    (root / "logs" / "app.log").write_text("user a@b.com token=SECRET\n", encoding="utf-8")
    (root / "user_data.json").write_text(json.dumps({"accounts": ["owner"]}), encoding="utf-8")
    (root / "identity.json").write_text(json.dumps({"device_id": "dev-abc", "status": "ACTIVE"}), encoding="utf-8")
    return root


def test_fault_catalog_lookup():
    assert "FC-BATT-001" in list_codes()
    hit = lookup("FC-BATT-001")
    assert hit["ok"] is True
    assert lookup("FC-NOPE")["ok"] is False


def test_spares_never_invent_stock_or_price():
    mapped = map_spares("FC-BATT-001", sku="handheld_hybrid")
    assert mapped["ok"] is True
    assert mapped["stock_qty"] == UNKNOWN
    assert mapped["unit_price"] == UNKNOWN
    assert mapped["parts"]
    for part in mapped["parts"]:
        assert part["stock_qty"] == UNKNOWN
        assert part["unit_price"] == UNKNOWN
        assert part["lead_time_weeks"] == UNKNOWN
        assert part["moq"] == UNKNOWN


def test_rma_state_machine_and_warranty_external(tmp_path):
    desk = RmaSupportDesk(tmp_path / "rma.json")
    opened = desk.open_case(
        device_id="dev-1",
        serial="DEVTEST-GX1-L1-000001-A",
        sku="handheld_hybrid",
        fault_code="FC-DISP-001",
        symptom="cracked_screen",
    )
    assert opened["ok"] is True
    case_id = opened["case"]["case_id"]
    assert opened["case"]["commercial_warranty"] == "EXTERNAL"
    assert desk.transition(case_id, "CLOSED")["ok"] is False
    assert desk.transition(case_id, "DIAGNOSED")["ok"] is True
    ext = desk.transition(case_id, "WARRANTY_EXTERNAL", note="commercial terms EXTERNAL")
    assert ext["ok"] is True
    hist = desk.service_history(case_id)
    assert hist["state"] == "WARRANTY_EXTERNAL"
    assert len(hist["history"]) >= 3


def test_rma_diagnostic_repair_transfer_wipe(tmp_path):
    desk = RmaSupportDesk(tmp_path / "rma.json")
    opened = desk.open_case(
        device_id="dev-1",
        serial="DEVTEST-GX1-L1-000001-A",
        sku="dock",
        fault_code="FC-DOCK-001",
        symptom="no_detect",
    )
    case_id = opened["case"]["case_id"]
    old_root = _device_root(tmp_path, "old")
    bundle = desk.attach_diagnostic_bundle(case_id, old_root, tmp_path / "bundle.tar.gz")
    assert bundle["ok"] is True
    desk.transition(case_id, "DIAGNOSED")
    desk.transition(case_id, "AUTHORIZED")
    desk.transition(case_id, "RECEIVED")
    repair = desk.enter_repair_mode(case_id, old_root)
    assert repair["ok"] is True
    new_root = tmp_path / "new"
    xfer = desk.replacement_transfer(case_id, REPO_ROOT, old_root, new_root)
    assert xfer["ok"] is True
    wipe = desk.wipe_for_return(case_id, old_root)
    assert wipe["ok"] is True
    assert wipe["physical_media_sanitize"] == "EXTERNAL"
    window = desk.support_window("gunnchos-device-os", "0.xv")
    assert window["business_year_commitments"] == "EXTERNAL_PENDING"
