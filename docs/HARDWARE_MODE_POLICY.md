# Hardware Mode Policy

**Status:** implemented in software · **not hardware-validated**

**Code:** `gunnchos_device_os/hardware_mode_policy.py`  
**Rules:** `config/hardware_compatibility_rules.yaml`  
**Engine:** `gunnchos_device_os/hardware_compatibility_engine.py`

---

## Purpose

Define which OS modes are allowed, warned, or blocked per device class based on loaded hardware profiles and global compatibility rules.

---

## Mode evaluation flow

```
load_device_profile(device_id)
    → mode_policy.check_mode(device_id, mode)
    → compatibility_engine (blocked combos, wearables rules)
    → CompatibilityResult (pass | warn | fail + fallbacks)
```

---

## Global rules

| Rule | Applies to | Behavior |
|------|------------|----------|
| Mode in `supported_modes` | all | fail if absent; suggest first supported mode as fallback |
| Wearables + Developer | `wearables_arena_set` | **block** — unrestricted developer not allowed |
| Wearables + Workshop | `wearables_arena_set` | **block** |
| Wearables + spaceship | `wearables_arena_set` | **block** without marshal → fallback arcade |
| Wearables Play/Arcade | `wearables_arena_set` | **warn** if no marshal_control in venue |
| Journey preset not in profile | all | warn; fallback to first preset |

---

## Per-class mode summary

| Mode | Student 14.5 | Handheld | DS-XL | Wearables |
|------|:------------:|:--------:|:-----:|:---------:|
| School | ✓ | ✓ | ✓ | ✓ |
| Developer | ✓ | limited | ✓ | **✗** |
| Play / Arcade | ✓ | ✓ | — | ✓ (marshal) |
| Workshop / Laboratory | ✓ | limited | ✓ | **✗** |
| Guardian / Library / Offline | ✓ | ✓ | ✓ | ✓ |
| Admin | ✓ | — | ✓ | ✓ |

Full matrix: [../hardware_compat/DEVICE_CLASS_COMPATIBILITY_MATRIX.md](../hardware_compat/DEVICE_CLASS_COMPATIBILITY_MATRIX.md)

---

## Fallback policy

When a mode fails:

1. Return explicit blocker message.
2. Suggest profile-appropriate fallback (e.g. `school`, `arcade`, `marshal_controlled_arcade`).
3. Attach evidence tag `real_hardware_validation_required`.

Fallbacks are **software suggestions** — not proven UX on hardware.

---

## Guardian and consent interactions

Modes that enable research, deploy, or elevated access may require:

- `consent=True` for telemetry/research paths
- `guardian_approved=True` for youth deploy or restricted features
- `marshal_control=True` for arena play on wearables

Evaluated in `hardware_compatibility_engine.py`.

---

## Related documents

- [DEVICE_SPECIFIC_OS_BEHAVIOR.md](DEVICE_SPECIFIC_OS_BEHAVIOR.md)
- [MODE_POLICY_MATRIX.md](MODE_POLICY_MATRIX.md) (general OS modes)
- [../hardware_compat/HARDWARE_CLAIM_BOUNDARY.md](../hardware_compat/HARDWARE_CLAIM_BOUNDARY.md)
