# Hardware Power and Thermal Policy

**Status:** implemented in software · **not hardware-validated**

**Code:** `gunnchos_device_os/hardware_power_policy.py`, `gunnchos_device_os/hardware_thermal_policy.py`  
**Hardware references:** `../gunnchos-hardware-industrial-design/dvt/DVT_BATTERY_TEST_PLAN.md`, `dvt/DVT_THERMAL_TEST_PLAN.md`, `architecture/POWER_TREE.md`, `product/PERFORMANCE_TARGETS.md`

---

## Purpose

Define battery class expectations, low-power behavior, and thermal throttle policies per device profile. Policies express **targets** until DVT reports are linked.

---

## Battery classes

| Class | Device(s) | Profile intent |
|-------|-----------|----------------|
| `school_day` | Student 14.5 | Full school day on typical student load |
| `portable_extended` | Handheld Hybrid | Extended portable play sessions |
| `workstation_portable` | DS-XL Coder | Developer sessions with compile loads |
| `wearable_short_cycle` | Wearables / Arena | Short arena/wearable cycles |

---

## Thermal classes

| Class | Device(s) | Throttle policy |
|-------|-----------|-----------------|
| `passive_fanless` | Student 14.5 | `balanced` |
| `active_cooling` | Handheld, DS-XL | `gaming_balanced` / `developer` |
| `strict_throttle` | Wearables / Arena | `arena_safe` |

---

## Per-class summary

| Attribute | Student 14.5 | Handheld | DS-XL | Wearables |
|-----------|:------------:|:--------:|:-----:|:---------:|
| Battery class | school_day | portable_extended | workstation_portable | wearable_short_cycle |
| Thermal class | passive_fanless | active_cooling | active_cooling | strict_throttle |
| Throttle policy | balanced | gaming_balanced | developer | arena_safe |
| Fan assumption | none | active | active | minimal / strict cap |

---

## OS policy behaviors (intended)

### Power

- Low-battery warnings before critical shutdown threshold (profile-tuned, not calibrated).
- School mode may prefer power-save defaults on Student 14.5.
- Wearables: aggressive sleep between arena rounds.
- Docked operation may bypass battery runtime checks for display policy (not power delivery validated).

### Thermal

- **balanced** — Limit sustained CPU/GPU for fanless chassis (Student).
- **gaming_balanced** — Allow higher peaks with active cooling; throttle under gaming load (Handheld).
- **developer** — Favor compile/build sustained performance with cooling (DS-XL).
- **arena_safe** — Hard cap for venue safety and short-cycle battery (Wearables).

---

## Hardware repo test alignment

| Hardware plan | OS policy area | Evidence |
|---------------|----------------|----------|
| `dvt/DVT_BATTERY_TEST_PLAN.md` | runtime baselines | **none** |
| `dvt/DVT_THERMAL_TEST_PLAN.md` | throttle under load | **none** |
| `certification/UN38_3_BATTERY_READINESS.md` | shipping / safety | not certified |
| `mechanical_correctness/BATTERY_COMPARTMENT_FIT_CHECK.md` | mechanical fit | placeholder |

QA handoff: `qa/BATTERY_THERMAL_TEST_HANDOFF.md`

---

## Known gaps

| Gap | Devices |
|-----|---------|
| `physical_thermal_validation_pending` | Student 14.5 |
| `battery_validation_pending` | Handheld Hybrid |
| No DVT logs | all |

See [HARDWARE_COMPATIBILITY_GAP_ANALYSIS.md](HARDWARE_COMPATIBILITY_GAP_ANALYSIS.md).

---

## Boot readiness linkage

Simulated boot checks `battery_policy_available` and `thermal_policy_available` from profile flags — confirms **policy presence**, not hardware measurement.

`boot_readiness/BOOT_READINESS_STATUS.md`

---

## Claim boundary

Power and thermal policies are **software mirrors of hardware targets**. They do not prove battery life, thermal safety, or UN38.3 compliance.
