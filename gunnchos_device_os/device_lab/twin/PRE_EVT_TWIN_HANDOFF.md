# Pre-EVT Digital Twin Infrastructure — Handoff

**Status:** SCHEMA + HANDOFF PREPARED — `PHYSICAL_PENDING` for VF4/VF5/VF6  
**Token:** `GUNNCHDEVICE_LAB_PRE_EVT_TWIN_INFRA_COMPLETE` may become true only when
schemas, linkage contracts, and Lab handoff paths are executable digitally.
This does **not** imply EVT calibration, HIL, or physical correlation.

## Claim firewall

| Flag | Value |
|------|-------|
| SILICON_EXACT_EMULATION | false |
| VF4 | PHYSICAL_PENDING |
| VF5 | PHYSICAL_PENDING |
| VF6 | PHYSICAL_PENDING |
| RING_SPATIAL_ACCURACY | SIMULATED |
| PRODUCTION_READY | false |

## Schemas (Lab)

Located under `gunnchos_device_os/device_lab/schemas/`:

- `calibration_bridge.schema.json`
- `calibration_ingestion.schema.json`
- `metric_mapping.schema.json`
- `evidence_linkage.schema.json`
- `prediction_vs_measurement.schema.json`
- `physical_test_id.schema.json`
- `device_profile.schema.json`

Wave 5 adds twin handoff contract: `gunnchos_device_os/device_lab/twin/pre_evt_twin_handoff.schema.json`.

## Digital handoff path (pre-EVT)

1. Lab session produces `run_manifest.json` + scenario evidence under `artifacts/device_lab/`.
2. Measurement classes must be labeled (`HOST_OBSERVED`, `GUEST_OBSERVED`, `VIRTUAL_CONSTRAINED`, `MODELED_FROM_PUBLIC_SPEC`, `SYNTHETIC_SCENARIO`).
3. `CALIBRATED_EVT` / `PHYSICAL_MEASURED` remain unavailable until EVT hardware.
4. Ecosystem ECO evidence lands under `artifacts/device_lab/ecosystem/`.
5. Chaos evidence lands under `artifacts/device_lab/chaos/`.

## Blocked on EVT

- LAB-FUTURE-007 EVT0 calibration
- LAB-FUTURE-008 hardware-in-the-loop
- LAB-FUTURE-009 simulator-vs-physical correlation

## Operator commands

```bash
gunnchctl ecosystem start --preset full
gunnchctl ecosystem test ECO-001
gunnchctl chaos suite --device handheld_hybrid
gunnchctl score
```
