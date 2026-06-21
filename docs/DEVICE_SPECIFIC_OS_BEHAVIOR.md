# Device-Specific OS Behavior

**Status:** documented from profiles · **not proven on physical hardware**

Index of per-SKU OS behavior documents. All behavior described here is **profile- and policy-driven** unless linked lab evidence states otherwise.

**Hardware repo:** [`../gunnchos-hardware-industrial-design`](../gunnchos-hardware-industrial-design)

---

## Device behavior documents

| Device class | Document | Profile |
|--------------|----------|---------|
| Student 14.5 | [STUDENT_14_5_OS_BEHAVIOR.md](STUDENT_14_5_OS_BEHAVIOR.md) | `hardware_compat/device_profiles/student_14_5.yaml` |
| Handheld Hybrid | [HANDHELD_HYBRID_OS_BEHAVIOR.md](HANDHELD_HYBRID_OS_BEHAVIOR.md) | `hardware_compat/device_profiles/handheld_hybrid.yaml` |
| DS-XL Coder | [DS_XL_CODER_OS_BEHAVIOR.md](DS_XL_CODER_OS_BEHAVIOR.md) | `hardware_compat/device_profiles/ds_xl_coder.yaml` |
| Wearables / Arena | [WEARABLES_ARENA_OS_BEHAVIOR.md](WEARABLES_ARENA_OS_BEHAVIOR.md) | `hardware_compat/device_profiles/wearables_arena_set.yaml` |

---

## Cross-cutting hardware policy docs

| Policy area | Document | Code module |
|-------------|----------|-------------|
| Mode availability and fallbacks | [HARDWARE_MODE_POLICY.md](HARDWARE_MODE_POLICY.md) | `hardware_mode_policy.py` |
| Input and display | [HARDWARE_INPUT_DISPLAY_POLICY.md](HARDWARE_INPUT_DISPLAY_POLICY.md) | `hardware_input_policy.py`, `hardware_display_policy.py` |
| Power and thermal | [HARDWARE_POWER_THERMAL_POLICY.md](HARDWARE_POWER_THERMAL_POLICY.md) | `hardware_power_policy.py`, `hardware_thermal_policy.py` |
| Storage and network | [HARDWARE_STORAGE_NETWORK_POLICY.md](HARDWARE_STORAGE_NETWORK_POLICY.md) | `hardware_storage_policy.py`, `hardware_network_policy.py` |

---

## Shared behavior principles

1. **Profile-first** — Capability checks load YAML profile before applying mode/preset/app-pack rules.
2. **Honest fallbacks** — Unsupported combinations return blockers, warnings, and suggested fallback presets/modes.
3. **Guardian and marshal gates** — Youth safety and arena marshal controls apply where profiles require them.
4. **Offline-first** — All four classes declare offline capability; network policy still governs sync behavior.
5. **Evidence tag** — Compatibility engine adds `real_hardware_validation_required` until lab evidence is linked.

---

## Hardware repo anchors

| Topic | Hardware path |
|-------|---------------|
| Product intent | `product/PRD_GUNNCHOS_MODULAR_CONSOLE_ECOSYSTEM.md` |
| SKU comparison | `architecture/DEVICE_COMPARISON_MATRIX.md` |
| OS contract | `docs/OS_HARDWARE_CONTRACT.md` |
| Mechanical class | `mechanical_correctness/device_mechanical_targets.json` |

---

## Claim boundary

Device-specific behavior docs describe **intended OS behavior when the profile matches**. They do not prove that behavior on shipped hardware. See [../hardware_compat/HARDWARE_CLAIM_BOUNDARY.md](../hardware_compat/HARDWARE_CLAIM_BOUNDARY.md).
