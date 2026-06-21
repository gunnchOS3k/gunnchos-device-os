# Hardware Profile Detection Plan

**Status:** plan documented · **automatic detection not implemented on hardware**

---

## Objective

Map physical hardware signals to OS `device_id` and load the correct YAML profile from `hardware_compat/device_profiles/`.

---

## Canonical ID map

| Hardware repo key (`device_mechanical_targets.json`) | OS `device_id` | Notes |
|------------------------------------------------------|----------------|-------|
| `student_14` | `student_14_5` | **Naming mismatch** — preserve explicit mapping |
| `handheld_hybrid` | `handheld_hybrid` | aligned |
| `ds_xl_coder` | `ds_xl_coder` | aligned |
| `wearables_arena_set` | `wearables_arena_set` | aligned |

Manufacturing packages use OS-style names in paths (e.g. `manufacturing/student_14_5/`) while JSON uses `student_14`. Detection layer must reconcile both.

---

## Detection signal sources (planned)

| Signal | Priority | Use |
|--------|----------|-----|
| SMBIOS / ACPI system SKU string | P0 | Primary match table |
| Device tree compatible string (ARM path) | P0 | Embedded variants |
| Panel EDID + touch HID combo | P1 | Disambiguate similar form factors |
| Dual-display presence | P1 | Strong signal for DS-XL |
| Controller-default HID without keyboard | P1 | Handheld hint |
| eMMC size tier ≤64 GB + no dock | P2 | Wearables hint |
| User first-run selection | P3 | Fallback when ambiguous |

---

## Detection algorithm (planned)

```
1. Collect hardware IDs from firmware/ACPI/DT
2. Lookup in detection_table.yaml (future config)
3. If single match → bind profile
4. If multiple matches → prompt user (first-run)
5. If no match → safe mode + manual profile select (recovery)
6. Persist binding to local hardware binding store
7. Log binding decision for audit
```

Current code: `hardware_capability_detector.detect(device_id)` requires explicit ID.

---

## Confidence levels

| Level | Meaning | Action |
|-------|---------|--------|
| high | Unique SKU match | Auto-bind |
| medium | Heuristic match | Bind + show confirm once |
| low | Ambiguous | User select at first run |
| none | Unknown | Safe mode; no mode claims |

---

## Hardware repo inputs

| Artifact | Use |
|----------|-----|
| `mechanical_correctness/device_mechanical_targets.json` | Expected class labels |
| `architecture/DEVICE_COMPARISON_MATRIX.md` | SKU differentiators |
| `manufacturing/*/factory_test_script.py` | Factory SKU programming reference |
| `dvt/DVT_SOFTWARE_HARDWARE_INTEGRATION_PLAN.md` | Integration test cases |

---

## Test cases (when hardware available)

| Case | Input | Expected `device_id` |
|------|-------|-------------------|
| DT-001 | Student reference board SMBIOS | `student_14_5` |
| DT-002 | Handheld with gamepad, no KB | `handheld_hybrid` |
| DT-003 | Dual panel detected | `ds_xl_coder` |
| DT-004 | Wearable eMMC profile | `wearables_arena_set` |
| DT-005 | Unknown board | safe mode, no auto claim |

---

## Related documents

- [FIRST_RUN_HARDWARE_BINDING.md](FIRST_RUN_HARDWARE_BINDING.md)
- [BOOT_FAILURE_FALLBACKS.md](BOOT_FAILURE_FALLBACKS.md)
- [../docs/HARDWARE_COMPATIBILITY_GAP_ANALYSIS.md](../docs/HARDWARE_COMPATIBILITY_GAP_ANALYSIS.md) (GAP-013)

---

## Claim boundary

Detection plan is **design only**. No automatic hardware SKU detection is proven today.
