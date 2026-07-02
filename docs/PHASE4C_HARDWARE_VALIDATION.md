# Phase 4C: Reference Hardware Validation Package

## Claim boundary

**This package prepares reference hardware validation workflows — it does NOT claim physical hardware validation unless a filled report with `physical_validation_performed: true` exists from real target device testing.**

Container/kiosk evidence remains **container-only** and cannot close the physical hardware validation beta blocker.

## What was implemented

| Component | Path |
|-----------|------|
| Reference device matrix | `hardware_validation/reference_device_matrix.yaml` |
| Report template | `hardware_validation/reference_device_report.template.md` |
| Container-only example | `hardware_validation/reference_device_report.example.md` |
| Safe host info collector | `scripts/collect_reference_hardware_info.py` |
| Report validator | `scripts/validate_hardware_report.py` |
| Claim boundary | `hardware_validation/HARDWARE_CLAIM_BOUNDARY.md` |

## Validation areas tracked

- Platform: CPU, RAM, storage
- Display / input: resolution, touchscreen, keyboard, controller
- Network: Wi-Fi, Bluetooth
- Media: audio, microphone, camera, USB-C display
- Power: battery, thermals, sleep/wake, suspend/resume
- Software: launcher startup, workspace persistence, media, games, accessibility

## Reference target SKUs

| Device ID | Profile |
|-----------|---------|
| `student_14_5` | `hardware_compat/device_profiles/student_14_5.yaml` |
| `handheld_hybrid` | `hardware_compat/device_profiles/handheld_hybrid.yaml` |
| `ds_xl_coder` | `hardware_compat/device_profiles/ds_xl_coder.yaml` |
| `wearables_arena_set` | `hardware_compat/device_profiles/wearables_arena_set.yaml` |

All target SKUs remain `not_started` for physical validation until lab reports are filed.

## Commands

```bash
# Collect safe host snapshot (no private IDs)
python3 scripts/collect_reference_hardware_info.py --output /tmp/host_snapshot.json

# Validate matrix, template, and example report
python3 scripts/validate_hardware_report.py

# Run package tests
pytest -q tests/test_reference_hardware_validation.py
```

## Filling a real hardware report

1. Copy `hardware_validation/reference_device_report.template.md` to a dated report path.
2. Run the collector on the test host: `python3 scripts/collect_reference_hardware_info.py --output evidence/host_snapshot.json`
3. Complete the subsystem checklist on **physical target hardware**.
4. Set sign-off YAML with `validation_environment: physical` and `physical_validation_performed: true` only after real device testing.
5. Update `reference_device_matrix.yaml` with the report path and area statuses.
6. Run `python3 scripts/validate_hardware_report.py path/to/report.md`.

## What is NOT implemented

- Physical lab execution on GunnchOS target SKUs
- Automated hardware-in-the-loop test harness
- Fleet-wide hardware certification
- Secure boot / TPM validation on device

## Beta gate

`hardware_evidence` status remains **prototype** — container evidence paragraph plus validation package scaffolding. Physical validation blocker is **not closed**.

## Related

- [HARDWARE_CLAIM_BOUNDARY.md](../hardware_validation/HARDWARE_CLAIM_BOUNDARY.md)
- [CONTAINER_KIOSK_VALIDATION_LOG.md](../hardware_validation/CONTAINER_KIOSK_VALIDATION_LOG.md)
- [REFERENCE_HARDWARE_VALIDATION_TEMPLATE.md](../hardware_validation/REFERENCE_HARDWARE_VALIDATION_TEMPLATE.md) (legacy template)
