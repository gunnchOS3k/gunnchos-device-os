"""Evaluate the factory/RMA/support STREAM as DIGITAL_PREPARATION."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from gunnchos_device_os.ops.claim import (
    CLAIM_BOUNDARY,
    COMMERCIAL_WARRANTY,
    EXTERNAL_ITEMS,
    PRODUCTION_RELEASE_CLAIMED,
)
from gunnchos_device_os.ops.first_use import FirstUseFlow
from gunnchos_device_os.ops.rma import RmaSupportDesk
from gunnchos_device_os.release_engineering.factory_provisioning import FactoryProvisioningStation


def evaluate(repo_root: Path, out_path: Path | None = None) -> dict[str, Any]:
    repo_root = Path(repo_root)
    with tempfile.TemporaryDirectory(prefix="factory_rma_eval_") as tmp:
        tmp_path = Path(tmp)
        station = FactoryProvisioningStation(repo_root, tmp_path / "factory_store.json")
        provision = station.provision_new_device()
        device_id = provision["device_id"]
        test = station.import_test_result(
            device_id,
            {
                "device_id": device_id,
                "station_id": "STATION-1",
                "suite_id": "FINAL_QA",
                "result": "PASS",
                "timestamp_utc": "2026-08-13T00:00:00Z",
                "measurements": {"boot_probe_ms": 400},
            },
        )
        record = station.export_device_record(device_id)
        wipe = station.factory_secure_wipe(device_id, reason="eval")

        desk = RmaSupportDesk(tmp_path / "rma_store.json")
        case = desk.open_case(
            device_id=device_id,
            serial=provision["serial"],
            sku="handheld_hybrid",
            fault_code="FC-BATT-001",
            symptom="eval",
        )
        desk.transition(case["case"]["case_id"], "DIAGNOSED", note="eval")
        desk.transition(case["case"]["case_id"], "WARRANTY_EXTERNAL", note="commercial warranty EXTERNAL")

        first = FirstUseFlow(tmp_path / "first_use.json")
        first_result = first.run_default_offline_student("eval-1")

        cert_status = record["record"]["device"]["cert_request"]["status"] if record.get("ok") else None
        esim_status = provision.get("esim_status")

        digital_ok = all(
            [
                provision.get("ok"),
                test.get("ok"),
                record.get("ok"),
                wipe.get("ok"),
                case.get("ok"),
                first_result.get("ok"),
                cert_status == "EXTERNAL_PENDING",
                esim_status == "EXTERNAL_PENDING",
                PRODUCTION_RELEASE_CLAIMED is False,
            ]
        )
        report = {
            "schema": "gunnchos.ops.factory_rma_support.eval.v1",
            "ok": digital_ok,
            "status": "DIGITAL_PREPARATION" if digital_ok else "INCOMPLETE_DIGITAL",
            "PRODUCTION_RELEASE_CLAIMED": False,
            "commercial_warranty": COMMERCIAL_WARRANTY,
            "cursor_merges": False,
            "factory": {
                "provision_ok": provision.get("ok"),
                "cert_request": cert_status,
                "esim": esim_status,
                "test_import_ok": test.get("ok"),
                "device_record_ok": record.get("ok"),
                "secure_wipe_ok": wipe.get("ok"),
                "physical_media_sanitize": wipe.get("physical_media_sanitize"),
            },
            "rma": {
                "case_ok": case.get("ok"),
                "warranty_path": "WARRANTY_EXTERNAL",
            },
            "first_use": {"ok": first_result.get("ok"), "status": first_result["session"]["status"]},
            "external": list(EXTERNAL_ITEMS),
            "claim_boundary": CLAIM_BOUNDARY,
        }
        dest = out_path or (repo_root / "artifacts" / "factory_rma" / "VP_FACTORY_RMA_SUPPORT_DIGITAL.json")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        report["artifact"] = str(dest)
        return report
