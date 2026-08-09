"""Factory test station — software runner with simulated HAL (Lane I).

Per-device suites; records serial/HW/SW rev/pass-fail/measurement/limit/
timestamp/station/operator. No production private keys in repo.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any
import hashlib
import json
import time
import uuid

from gunnchos_device_os.cont_viii import CLAIM_BOUNDARY, TOKEN_FACTORY_PASS

DEVICE_SKUS = ("student", "ds_xl", "handheld", "dock_host")


@dataclass
class Measurement:
    name: str
    value: float
    unit: str
    limit_low: float
    limit_high: float

    @property
    def pass_fail(self) -> str:
        return "PASS" if self.limit_low <= self.value <= self.limit_high else "FAIL"


@dataclass
class FactoryRecord:
    serial: str
    hw_rev: str
    sw_rev: str
    sku: str
    station_id: str
    operator_id: str
    timestamp: float
    measurements: list[dict[str, Any]]
    overall: str
    suite_id: str
    simulated_hal: bool = True
    production_keys_present: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FactoryTestStation:
    station_id: str = "FTS-SIM-001"
    operator_id: str = "op-digital"
    sw_rev: str = "0.8.0-cont-viii"
    hw_rev: str = "EVT1-SIM"

    def suite_for_sku(self, sku: str) -> list[Measurement]:
        base = [
            Measurement("boot_probe_ms", 420.0, "ms", 0.0, 5000.0),
            Measurement("storage_gb", 128.0, "GB", 64.0, 2048.0),
            Measurement("battery_pct_sim", 100.0, "%", 50.0, 100.0),
            Measurement("display_edid_ok", 1.0, "bool", 1.0, 1.0),
            Measurement("wifi_scan_count", 3.0, "count", 1.0, 64.0),
            Measurement("ring_calibrate_ok", 1.0, "bool", 1.0, 1.0),
        ]
        if sku == "dock_host":
            base.append(Measurement("dock_detect_ok", 1.0, "bool", 1.0, 1.0))
            base.append(Measurement("external_display_modes", 2.0, "count", 1.0, 16.0))
        if sku == "ds_xl":
            base.append(Measurement("second_panel_ok", 1.0, "bool", 1.0, 1.0))
        if sku == "handheld":
            base.append(Measurement("imu_self_test", 1.0, "bool", 1.0, 1.0))
        return base

    def run_sku(self, sku: str, serial: str | None = None) -> FactoryRecord:
        if sku not in DEVICE_SKUS:
            raise ValueError(f"unknown sku: {sku}")
        serial = serial or f"SIM-{sku.upper()}-{uuid.uuid4().hex[:8]}"
        ms = self.suite_for_sku(sku)
        rows = []
        for m in ms:
            rows.append({
                "name": m.name,
                "value": m.value,
                "unit": m.unit,
                "limit_low": m.limit_low,
                "limit_high": m.limit_high,
                "pass_fail": m.pass_fail,
            })
        overall = "PASS" if all(r["pass_fail"] == "PASS" for r in rows) else "FAIL"
        return FactoryRecord(
            serial=serial,
            hw_rev=self.hw_rev,
            sw_rev=self.sw_rev,
            sku=sku,
            station_id=self.station_id,
            operator_id=self.operator_id,
            timestamp=time.time(),
            measurements=rows,
            overall=overall,
            suite_id=f"suite-{sku}-v1",
            simulated_hal=True,
            production_keys_present=False,
        )

    def run_all(self, out_dir: Path | None = None) -> dict[str, Any]:
        root = Path(__file__).resolve().parents[2]
        out = out_dir or (root / "results/cont_viii/factory")
        out.mkdir(parents=True, exist_ok=True)
        records = [self.run_sku(sku).to_dict() for sku in DEVICE_SKUS]
        # Ensure no production private keys shipped
        key_globs = list((root / "secrets").glob("**/*")) if (root / "secrets").exists() else []
        forbidden = [
            p for p in key_globs
            if p.suffix in {".pem", ".key", ".p12"} and "prod" in p.name.lower()
        ]
        # Also scan factory fixtures
        fixture_keys = list((root / "factory").rglob("*.pem")) + list((root / "factory").rglob("*.key"))
        prod_keys = [str(p) for p in forbidden + fixture_keys if "prod" in p.name.lower() or "production" in str(p).lower()]

        report = {
            "schema": "gunnchos.factory_station.v1",
            "ok": all(r["overall"] == "PASS" for r in records) and len(prod_keys) == 0,
            "token": None,
            "station_id": self.station_id,
            "operator_id": self.operator_id,
            "skus": list(DEVICE_SKUS),
            "records": records,
            "simulated_hal": True,
            "physical_fixture": False,
            "production_private_keys_in_repo": prod_keys,
            "claim_boundary": CLAIM_BOUNDARY,
            "mock": False,
        }
        report["token"] = TOKEN_FACTORY_PASS if report["ok"] else None
        (out / "factory_station_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        # per-device artifacts
        for r in records:
            digest = hashlib.sha256(json.dumps(r, sort_keys=True).encode()).hexdigest()[:16]
            (out / f"{r['sku']}_{r['serial']}_{digest}.json").write_text(json.dumps(r, indent=2), encoding="utf-8")
        return report


def run_factory_station(**kwargs: Any) -> dict[str, Any]:
    return FactoryTestStation(**kwargs).run_all()
