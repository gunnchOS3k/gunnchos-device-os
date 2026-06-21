# Hardware Compatibility Requirements

**Status:** YAML contract exists · **hardware compatibility not physically proven**

> Per-SKU compatibility gates for gunnchOS. Config: `config/device_classes.yaml`, `gunnchos_device_os/device_classes.py`. Physical validation requires hardware test reports — **not available today**.

---

## Device classes

| Class | ID | Deploy role | Physical validation |
|-------|-----|-------------|---------------------|
| Student 14.5 | `student_14_5` | target | **not_started** |
| Handheld Hybrid | `handheld_hybrid` | target | **not_started** |
| DS-XL Coder | `ds_xl_coder` | source_and_target | **not_started** |
| Wearables / Arena Set | `wearables_arena_set` | future_target_placeholder | **not_started** |

---

## Compatibility dimensions (all SKUs)

Each SKU must document pass/fail (or N/A) for:

| Dimension | Gate |
|-----------|------|
| Display | Resolution, DPI, rotation, docked external display |
| Input | Keyboard, touch, stylus, controller |
| Controller | Mapping, rumble, battery (handheld) |
| Touch | Multi-touch, palm rejection |
| Keyboard | Layout, backlight, function keys |
| Dock | USB-C display, power, Ethernet |
| Network | Wi-Fi, Bluetooth, offline fallback |
| Storage | Min free space, NVMe health signal |
| Battery | Runtime baseline, low-battery policy |
| Thermal | Throttle profile under load |
| Audio | Speaker, headset, mic privacy LED |
| Camera / mic | Hardware mute, indicator, guardian policy |
| Sensors | Accelerometer, ambient (wearables) |
| Recovery path | USB recovery, safe mode |
| Performance profile | Mode-specific CPU/GPU caps |

---

## Student 14.5

| Attribute | Target (from device class contract) |
|-----------|--------------------------------------|
| Display | 14.5″, 1920×1200 |
| Input | Keyboard, touch, stylus |
| RAM target | 8 GB minimum (16 GB product target) |
| Primary modes | School, Developer, Play, Media, Studio, Guardian, Library, Offline |
| Special gates | WSL dev path, webcam/mic for remote learning, dock to external display |
| Evidence needed | Install + mode switch + WSL dry-run on reference hardware |

---

## Handheld Hybrid

| Attribute | Target |
|-----------|--------|
| Form | Portable console, dockable |
| Input | Controller-first, touch secondary |
| Primary modes | School, Play, Developer, Media, Workshop, Offline |
| Special gates | Steam launch route (mock until partner evidence), dock to TV, LAN play |
| Evidence needed | Controller mapping, thermal under gaming load, battery runtime test |

---

## DS-XL Coder

| Attribute | Target |
|-----------|--------|
| Form | Dual-screen handheld |
| Input | Keyboard-first |
| Primary modes | Developer, Coder, Workshop, Laboratory, Research Measurement |
| Deploy role | **Source** for deploy to other targets (`deploy_contract.py`) |
| Special gates | Deploy transports (Wi-Fi, USB-C, offline bundle), Edge-IO consent |
| Evidence needed | End-to-end deploy demo on real transport (currently mock API) |

---

## Wearables / Arena Set

| Attribute | Target |
|-----------|--------|
| Status | **future_target_placeholder** |
| Input | Touch, gesture, BLE wearables |
| Primary modes | Play, School, Offline, Library |
| Special gates | Edge-IO arena sessions, accessibility-first micro tasks |
| Evidence needed | BLE pairing, arena consent flow, field pilot waiver for GA |

---

## Compatibility matrix artifact

Before RC: draft matrix with YAML contract cross-check.  
Before GA: signed report per SKU with test logs attached to [../release_artifacts/ARTIFACT_MANIFEST_REQUIRED.md](../release_artifacts/ARTIFACT_MANIFEST_REQUIRED.md).

---

## Claim boundary

Hardware compatibility **requirements** are defined from software contracts. The repo does **not** claim hardware-validated release or that all dimensions are proven on physical devices.
