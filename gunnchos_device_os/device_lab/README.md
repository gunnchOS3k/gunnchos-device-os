# gunnchDevice Lab — Foundation v0.1

Virtual Device & Ecosystem Simulator for gunnchOS (WP-003R / Class D approved).

## Tokens

```text
GUNNCHDEVICE_LAB_FOUNDATION = PART_OF_WP003R
GUNNCHDEVICE_LAB_FULL_PRODUCT_EXPANSION = NOT_ACTIVE
SILICON_EXACT_EMULATION = false
BEHAVIORAL_DEVICE_PROFILE = true
VF4/VF5/VF6 = PHYSICAL_PENDING
```

## CLI

```bash
PYTHONPATH=.:src python3 scripts/gunnchctl devices
PYTHONPATH=.:src python3 scripts/gunnchctl start handheld_docked
PYTHONPATH=.:src python3 scripts/gunnchctl test GOLDEN-04 --device handheld_docked
PYTHONPATH=.:src python3 scripts/gunnchctl test GOLDEN-06 --device dsxl_coder
PYTHONPATH=.:src python3 scripts/gunnchctl test GOLDEN-07 --device edge_io_rings --rings
PYTHONPATH=.:src python3 scripts/gunnchctl test GOLDEN-08 --device student_14_5 --offline
PYTHONPATH=.:src python3 scripts/gunnchctl ui --host 127.0.0.1 --port 8765
```

Or: `python3 -m gunnchos_device_os.device_lab …`

## Journey mapping

| Journey | Scenario | Profile |
|---------|----------|---------|
| GOLDEN-04 | LAB-SCENARIO-OFFICE-DOCK | handheld_docked |
| GOLDEN-06 | LAB-SCENARIO-DSXL-DUALSCREEN | dsxl_coder |
| GOLDEN-07 | LAB-SCENARIO-RING-REAL-INPUT | edge_io_rings (+ student host) |
| GOLDEN-08 | LAB-SCENARIO-LOCAL-AI-TUTOR | student_14_5 |

## Honesty

- CI default backend: `HYBRID_BEHAVIORAL` (real OS APIs + compositor/services).
- Full QEMU guest optional when tooling present; never claimed as SoC silicon replica.
- Implementer does **not** self-certify Independent PASS / V1.
- ADR-010: `docs/adr/ADR-010-gunnchDevice-Lab.md`

## WP-010 calibration interfaces (schema only)

- Physical test ID + calibration ingestion + metric map + prediction↔measurement + evidence linkage
- Instrument import adapters under `instrument_import/`
- Schemas in `schemas/*calibration*` / `physical_test_id.schema.json`
- **VF4/VF5/VF6 remain PHYSICAL_PENDING** — no CALIBRATED_EVT0; LAB-FUTURE-007 not executed
