# Device Class Compatibility Matrix

**Status:** profile-based matrix · **not hardware-validated**

Source profiles: `hardware_compat/device_profiles/*.yaml`  
Hardware comparison: `../gunnchos-hardware-industrial-design/architecture/DEVICE_COMPARISON_MATRIX.md`

Legend: **Y** = supported in profile · **N** = not supported · **W** = warn / conditional · **—** = N/A

---

## Device overview

| Attribute | Student 14.5 | Handheld Hybrid | DS-XL Coder | Wearables / Arena |
|-----------|:------------:|:---------------:|:-----------:|:-----------------:|
| `device_id` | `student_14_5` | `handheld_hybrid` | `ds_xl_coder` | `wearables_arena_set` |
| HW JSON key | `student_14` | `handheld_hybrid` | `ds_xl_coder` | `wearables_arena_set` |
| Deploy role | target | target | source_and_target | future_target_placeholder |
| Physical validation | not_started | not_started | not_started | not_started |

---

## Display

| Capability | Student 14.5 | Handheld Hybrid | DS-XL Coder | Wearables / Arena |
|------------|:------------:|:---------------:|:-----------:|:-----------------:|
| Primary display | 14.5″ 1920×1200 | 8.4″ 1920×1200 | 7.0″ 1280×720 | variable / wearable |
| Touch | Y | Y | Y | Y |
| Dual screen | N | N | Y | N |
| External display | Y | Y | Y | N |
| Dock DP Alt Mode | Y | Y | deploy source | N |

---

## Input

| Capability | Student 14.5 | Handheld Hybrid | DS-XL Coder | Wearables / Arena |
|------------|:------------:|:---------------:|:-----------:|:-----------------:|
| Built-in keyboard | Y | N (dock opt) | Y | N |
| Touch | Y | Y | Y (dual) | Y |
| Stylus | Y | N | N | N |
| Controller | N | Y | N | Y |
| Gesture / voice | N | N | N | W (placeholder) |

---

## Modes (selected)

| Mode | Student 14.5 | Handheld Hybrid | DS-XL Coder | Wearables / Arena |
|------|:------------:|:---------------:|:-----------:|:-----------------:|
| School | Y | Y | Y | Y |
| Developer | Y | W (light) | Y | **N** (blocked) |
| Play / Arcade | Y | Y | N | Y (marshal W) |
| Media | Y | Y | N | N |
| Studio / Workshop | Y | W | Y | **N** |
| Laboratory | Y | W | Y | N |
| Guardian | Y | Y | Y | Y |
| Library | Y | Y | Y | Y |
| Offline | Y | Y | Y | Y |
| Admin | Y | N | Y | Y |

Engine blockers: `wearables_arena_set` + Developer/Workshop; spaceship preset without marshal on wearables.

---

## Journey presets

| Preset | Student 14.5 | Handheld Hybrid | DS-XL Coder | Wearables / Arena |
|--------|:------------:|:---------------:|:-----------:|:-----------------:|
| scooter | Y | Y | Y | Y |
| bicycle | Y | Y | Y | Y |
| car / studio | Y | Y | Y | N |
| workshop / laboratory | Y | N | Y | N |
| spaceship | Y | N | Y | **N** (blocked) |
| arcade | N | Y | N | Y |
| guardian / library / offline | Y | Y | Y | Y |

---

## App packs (selected)

| App pack | Student 14.5 | Handheld Hybrid | DS-XL Coder | Wearables / Arena |
|----------|:------------:|:---------------:|:-----------:|:-----------------:|
| learn_pack | Y | Y | Y | Y |
| cs_student_pack | Y | W | Y | N |
| game_pack | N | Y | W | Y |
| research_pack | Y | W | Y | W |
| offline_essentials_pack | Y | Y | Y | Y |
| accessibility_essentials_pack | W | W | W | Y |

---

## Power and thermal

| Attribute | Student 14.5 | Handheld Hybrid | DS-XL Coder | Wearables / Arena |
|-----------|:------------:|:---------------:|:-----------:|:-----------------:|
| Battery class | school_day | portable_extended | workstation_portable | wearable_short_cycle |
| Thermal class | passive_fanless | active_cooling | active_cooling | strict_throttle |
| Throttle policy | balanced | gaming_balanced | developer | arena_safe |

**Validation:** profile targets only — no lab evidence linked.

---

## Storage and network

| Attribute | Student 14.5 | Handheld Hybrid | DS-XL Coder | Wearables / Arena |
|-----------|:------------:|:---------------:|:-----------:|:-----------------:|
| Storage class | NVMe ≥256 GB | NVMe ≥512 GB | NVMe ≥1 TB | eMMC ≥64 GB |
| RAM | 8 GB | 12 GB | 16 GB | 4 GB |
| Wi-Fi | Wi-Fi 6E | Wi-Fi 6E | Wi-Fi 6E | Wi-Fi 6 |
| Offline capable | Y | Y | Y | Y |
| Ethernet | dock optional | — | — | — |

---

## Developer / deploy features

| Feature | Student 14.5 | Handheld Hybrid | DS-XL Coder | Wearables / Arena |
|---------|:------------:|:---------------:|:-----------:|:-----------------:|
| WSL path | Y | N | Y | **N** |
| VS Code path | Y | W | Y | N |
| Deploy target | Y | N | Y | N |
| Deploy source | N | N | Y | N |
| Dual-screen workflow | N | N | Y | N |

---

## Known gaps (from profiles)

| Device | Gaps |
|--------|------|
| Student 14.5 | physical thermal validation pending; HLK not run |
| Handheld Hybrid | Steam not certified; battery validation pending |
| DS-XL Coder | dual-screen OS shell not proven on hardware |
| Wearables / Arena | arena safety not field validated; no WSL workstation |

---

## Related documents

- [HARDWARE_VALIDATION_STATUS.md](HARDWARE_VALIDATION_STATUS.md)
- [../docs/DEVICE_SPECIFIC_OS_BEHAVIOR.md](../docs/DEVICE_SPECIFIC_OS_BEHAVIOR.md)
- [../requirements/HARDWARE_COMPATIBILITY_REQUIREMENTS.md](../requirements/HARDWARE_COMPATIBILITY_REQUIREMENTS.md)
