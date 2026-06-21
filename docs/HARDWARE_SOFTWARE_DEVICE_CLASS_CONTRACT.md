# Hardware / Software Device Class Contract

**Status:** device OS alpha · YAML + Python validation  
**Modules:** `gunnchos_device_os/device_classes.py`  
**Config:** `config/device_classes.yaml`  
**Hardware cross-link:** [gunnchos-hardware-industrial-design](https://github.com/gunnchOS3k/gunnchos-hardware-industrial-design)

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## Purpose

This contract defines what the **software layer may assume** about each hardware SKU and what hardware teams must provide for a class to be considered compatible. It extends the summary in `docs/HARDWARE_SOFTWARE_CONTRACT.md` with per-field semantics tied to `device_classes.py`.

---

## Required fields

Every device class entry must include these keys (enforced by `validate_device_class()`):

| Field | Type | Software expectation |
|-------|------|---------------------|
| `device_id` | string | Stable identifier across deploy, mode, and fleet configs |
| `display_profile` | object | Size, resolution, PPI or size_class for layout scaling |
| `input_methods` | list | Launcher navigation and accessibility routing |
| `keyboard_support` | bool \| string | `true`, `false`, or `dock_optional` |
| `controller_support` | bool | Gamepad / HID navigation paths |
| `touch_support` | bool | Touch targets and gesture placeholders |
| `dock_support` | bool | External display and keyboard dock assumptions |
| `storage_class` | string | App pack and offline cache sizing hints |
| `ram_target_gb` | int | Mode performance tier planning |
| `performance_class` | string | Maps to mode `performance` keys in `modes.yaml` |
| `battery_class` | string | Power management policy placeholder |
| `thermal_class` | string | Throttling behavior placeholder |
| `supported_journey_presets` | list | Subset of `config/journey_presets.yaml` IDs |
| `supported_modes` | list | Subset of `config/modes.yaml` mode names |
| `supported_app_packs` | list | Subset of `config/app_packs.yaml` IDs |
| `accessibility_defaults` | object | Boot-time a11y hints for `accessibility_manager.py` |
| `offline_capabilities` | list | Advertised offline workflows |
| `deploy_role` | enum | `target`, `source_and_target`, `future_target_placeholder` |
| `hardware_contract_assumptions` | list | Non-enforced planning tags (Wi-Fi gen, TPM, etc.) |

Optional descriptive fields (not in `REQUIRED_FIELDS` but present in YAML):

- `display_name`, `primary_audience`, `main_workflows`, `input_style`

---

## Deploy role semantics

| Role | Meaning | Alpha behavior |
|------|---------|----------------|
| `target` | Receives packages from DS-XL or fleet admin | Listed in `config/deploy_targets.yaml` |
| `source_and_target` | Can build and receive packages | `ds_xl_coder` — default deploy source |
| `future_target_placeholder` | Documented only | No deploy target entry until hardware EVT |

---

## Software responsibilities

| Layer | Responsibility |
|-------|----------------|
| `device_classes.py` | Load, validate, expose class metadata |
| `mode_manager.py` | Filter modes by `supported_modes` (future enforcement) |
| `journey_preset_engine.py` | Filter presets by `supported_journey_presets` |
| `app_pack_manager.py` | Filter packs by `supported_app_packs` |
| `deploy_contract.py` | Map `device_id` → deploy target where applicable |
| `launcher_mock` | Visual device selector (simplified names) |

---

## Hardware responsibilities (planning)

| Signal | student_14_5 | handheld_hybrid | ds_xl_coder | wearables_arena_set |
|--------|--------------|-----------------|-------------|---------------------|
| Wi-Fi 6E | Assumed | Assumed | Assumed | Low-power variant |
| USB-C | Dock | Host + accessory | Host | N/A |
| TPM2 | Target | Target | Target | Future |
| Gamepad HID | No | Yes | No | Yes |
| External display | Via dock | Via dock | Yes | No |
| Active cooling | No (fanless) | Yes | Yes | Strict throttle |

**Not implemented in alpha:** ACPI battery API, thermal driver, dock hotplug events, secure boot attestation.

---

## Mode and preset compatibility matrix

| Class | Modes (subset) | Notable exclusions |
|-------|----------------|-------------------|
| student_14_5 | School, Developer, Play, Media, Studio, Guardian, Library, Offline, Admin | Research Measurement (use ds_xl_coder) |
| handheld_hybrid | School, Play, Developer, Media, Workshop, Offline, Admin | Guardian, Library (shared-device focus on other SKUs) |
| ds_xl_coder | Developer, Coder, Workshop, Laboratory, Research Measurement, Admin | Play, Media (not primary audience) |
| wearables_arena_set | Play, School, Offline, Library | Developer, Admin |

Guardian approval for restricted modes is enforced in `mode_policy.py`, not at the device class layer.

---

## Versioning and change control

1. Edit `config/device_classes.yaml`
2. Run `pytest tests/test_device_classes.py`
3. Update `docs/DEVICE_CLASSES.md` table if audience or workflows change
4. Sync hardware ID repo contract if physical SKU changes

Breaking changes to `device_id` require updates to `config/deploy_targets.yaml` and launcher `DEVICE_ID_MAP`.

---

## Claim boundary

| Allowed | Forbidden |
|---------|-----------|
| "Device class contract defines software assumptions for EVT-1 alpha" | "Certified hardware compatibility" |
| "Four classes validated by CI" | "All SKUs shipping" |
| "ds_xl_coder is deploy source in alpha mock" | "Production fleet provisioning" |

See `product/CLAIM_BOUNDARY.md`.
