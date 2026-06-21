# First-Run Hardware Binding

**Status:** plan documented · **not executed on hardware**

---

## Purpose

On first boot (or after factory reset), bind the running system to:

1. Detected or user-selected `device_id`
2. Loaded YAML profile from `hardware_compat/device_profiles/`
3. Default journey preset and accessibility defaults
4. Guardian/marshal policy baselines where applicable

---

## Binding flow (intended)

```
Boot → Detection (or prompt) → Confirm SKU → Write binding record → Apply profile policies → Continue setup wizard
```

---

## Binding record (planned fields)

| Field | Example |
|-------|---------|
| `device_id` | `student_14_5` |
| `hardware_repo_key` | `student_14` |
| `detection_confidence` | high / medium / low / manual |
| `detection_signals` | SMBIOS hash, panel EDID |
| `bound_at` | ISO timestamp |
| `profile_version` | git hash or semver of YAML |
| `first_run_complete` | boolean |

Storage location: TBD local secure store (not implemented).

---

## User confirmation rules

| Detection confidence | UX |
|---------------------|-----|
| high | Show SKU name; single confirm |
| medium | Show SKU + "Is this your device?" |
| low | Present picker with illustrations from hardware mechanical labels |
| none | Require admin/guardian select; log audit event |

Wearables / arena: default to supervised/marshal setup before Play mode unlock.

---

## Re-bind and migration

| Event | Behavior |
|-------|----------|
| Profile YAML update | Re-evaluate compatibility; warn on new blockers |
| Hardware board swap (RMA) | Clear binding; re-run detection |
| Wrong SKU bound | Recovery → profile picker in safe mode |

---

## Hardware repo alignment

| Hardware artifact | Binding use |
|-------------------|-------------|
| `mechanical_correctness/device_mechanical_targets.json` | Display labels in picker |
| `product/PRD_GUNNCHOS_MODULAR_CONSOLE_ECOSYSTEM.md` | SKU marketing names |
| `manufacturing/*/factory_test_procedure.md` | Factory-programmed SKU fields |

---

## Audit and guardian

- Guardian devices: log binding changes to guardian audit model (`docs/GUARDIAN_AUDIT_LOG_MODEL.md`).
- Arena devices: marshal role required to change binding in venue mode.

---

## Simulated behavior today

Boot readiness accepts explicit `device_id` parameter — no persistent binding store. First-run wizard exists at OS UX level separately from hardware binding.

---

## Claim boundary

First-run hardware binding is **design intent**. No production binding store or hardware-first-run test logs exist.
