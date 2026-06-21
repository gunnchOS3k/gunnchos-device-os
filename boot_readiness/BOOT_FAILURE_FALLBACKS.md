# Boot Failure Fallbacks

**Status:** fallback policy documented · **not hardware-tested**

---

## Purpose

Define degraded behavior when boot phases fail, without claiming unverified recovery success on silicon.

Related: [SAFE_MODE_AND_RECOVERY_PLAN.md](SAFE_MODE_AND_RECOVERY_PLAN.md), [../docs/HARDWARE_MODE_POLICY.md](../docs/HARDWARE_MODE_POLICY.md)

---

## Failure taxonomy

| Code | Failure | Tier |
|------|---------|------|
| BF-001 | Profile load fail | T0 |
| BF-002 | Detection ambiguous | T1 |
| BF-003 | Display init fail | T1 |
| BF-004 | Input init fail | T1 |
| BF-005 | Storage below minimum | T1 |
| BF-006 | Battery/thermal sensor missing | T1 |
| BF-007 | Unsupported mode at boot | T0/T1 |
| BF-008 | Update/rollback corrupt | T1 |
| BF-009 | Network required but unavailable | T0 |

---

## Fallback matrix

| Failure | Primary fallback | Secondary fallback | User message (intended) |
|---------|------------------|------------------|-------------------------|
| BF-001 | Safe mode | USB recovery | "Device profile unavailable" |
| BF-002 | User SKU picker | Safe mode | "Confirm your device model" |
| BF-003 | Safe mode (text) | External display if dock OK | "Display could not start" |
| BF-004 | Alternate input path | Safe mode | "Use touch/controller/keyboard" |
| BF-005 | Block non-essential modes | Cleanup wizard | "Storage low for this mode" |
| BF-006 | Policy defaults without telemetry | Warn + log | "Power/thermal sensors unavailable" |
| BF-007 | Mode policy fallback | School/offline default | From compatibility engine |
| BF-008 | Recovery partition / USB | Factory reset (admin) | "Recovery required" |
| BF-009 | Offline mode | Queue sync | "Working offline" |

---

## Mode-specific fallbacks (from engine)

| Device | Blocked combo | Fallback |
|--------|---------------|----------|
| wearables_arena_set | Developer | arcade / school |
| wearables_arena_set | Workshop | arcade |
| wearables_arena_set | spaceship w/o marshal | arcade |
| all | unsupported journey preset | first profile preset |

Source: `gunnchos_device_os/hardware_compatibility_engine.py`

---

## Display/input degraded layouts

| SKU | Degraded boot UI |
|-----|------------------|
| Student 14.5 | Single internal panel; keyboard nav |
| Handheld Hybrid | Touch if controller fail |
| DS-XL Coder | Single-screen coder layout if dual fail |
| Wearables / Arena | Minimal marshal/admin shell |

See [../docs/HARDWARE_INPUT_DISPLAY_POLICY.md](../docs/HARDWARE_INPUT_DISPLAY_POLICY.md).

---

## Simulated behavior today

T0 failures return `boot_ready_simulated: false` with failed check keys in API response. T1 hardware failures are **not instrumented**.

Example checks from `hardware_boot_readiness.py`:

- `display_available`
- `input_available`
- `storage_sufficient`
- `battery_policy_available`
- `thermal_policy_available`

---

## Logging (intended)

| Field | Content |
|-------|---------|
| `technical_log` | `boot_readiness_sim:device=… ready=…` |
| future HW log | failure code, fallback taken, detection confidence |

---

## Evidence required

Each fallback path needs integration test log on reference hardware before release claim. Track in `../hardware_release/HARDWARE_COMPATIBILITY_EVIDENCE_MATRIX.md`.

---

## Claim boundary

Fallback documentation describes **intended resilience**. It does not prove recovery success on physical devices.
