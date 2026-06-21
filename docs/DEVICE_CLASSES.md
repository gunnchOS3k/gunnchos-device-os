# Device Classes

**Status:** device OS alpha · config-driven hardware/software profiles  
**Source:** `gunnchos_device_os/device_classes.py`, `config/device_classes.yaml`

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## Overview

Device classes define the **hardware/software contract** between gunnchOS experience layers and planned gunnchos hardware SKUs. Each class specifies display, input, performance, supported journey presets, modes, app packs, accessibility defaults, offline capabilities, and deploy role.

The Python module validates required fields and loads YAML at runtime. This is **not** a shipping OS image or certified hardware specification.

---

## Device class table

| Device class | Primary audience | Main workflows | Input style | Supported modes | Deploy role |
|--------------|------------------|----------------|-------------|-----------------|-------------|
| **student_14_5** (Student 14.5) | K-12 and college students | Homework, essays, coding intro, research reading | Keyboard + touch | School, Developer, Play, Media, Studio, Guardian, Library, Offline, Admin | **target** |
| **handheld_hybrid** (Handheld Hybrid) | Middle school through gamer/creator | Portable learning, gaming, maker projects | Controller-first or touch | School, Play, Developer, Media, Workshop, Offline, Admin | **target** |
| **ds_xl_coder** (DS-XL Coder) | CS students, developers, researchers | Coding, deploy source, research measurement | Keyboard-first | Developer, Coder, Workshop, Laboratory, Research Measurement, Admin | **source_and_target** |
| **wearables_arena_set** (Wearables / Arena Set) | Pre-K exploration, arena events, future wearable pilots | Guided play, arena demos, accessibility-first micro tasks | Touch and gesture | Play, School, Offline, Library | **future_target_placeholder** |

---

## Per-class detail

### student_14_5

| Attribute | Value |
|-----------|-------|
| Display | 14.5″, 1920×1200, 157 PPI |
| Input methods | Keyboard, touch, stylus |
| RAM target | 8 GB |
| Storage | NVMe 256 GB |
| Performance | Balanced |
| Battery | School-day class |
| Journey presets | Scooter, Bicycle, Car, Studio, Guardian, Classroom, Library, Offline |
| App packs | learn_pack, write_pack, cs_student_pack, offline_essentials_pack |
| Offline | Offline lessons, writing, coding intro |
| Hardware assumptions | Wi-Fi 6E, USB-C dock, TPM2 target |

### handheld_hybrid

| Attribute | Value |
|-----------|-------|
| Display | 8.4″, 1920×1200, 270 PPI |
| Input methods | Touch, controller, keyboard dock (optional) |
| RAM target | 12 GB |
| Storage | NVMe 512 GB |
| Performance | Gaming balanced |
| Journey presets | Scooter, Bicycle, Car, Arcade, Workshop, Offline |
| App packs | learn_pack, game_pack, cs_student_pack, offline_essentials_pack |
| Hardware assumptions | Wi-Fi 6E, USB-C, gamepad HID |

### ds_xl_coder

| Attribute | Value |
|-----------|-------|
| Display | 15.6″, 2560×1600, 189 PPI |
| Input methods | Keyboard, touch, external display |
| RAM target | 16 GB |
| Storage | NVMe 1 TB |
| Performance | Developer |
| Journey presets | Workshop, Laboratory, Spaceship, Car, Offline |
| App packs | cs_student_pack, game_dev_pack, research_pack, stem_lab_pack |
| Deploy | Primary **source** for DS-XL → device deploy (`config/deploy_targets.yaml`) |
| Hardware assumptions | Wi-Fi 6E, USB-C host, WSL-capable host |

### wearables_arena_set

| Attribute | Value |
|-----------|-------|
| Display | Wearable or arena (variable resolution) |
| Input methods | Touch, gesture, controller, voice (placeholder) |
| RAM target | 4 GB |
| Storage | eMMC 64 GB |
| Performance | Edge-light |
| Deploy role | **future_target_placeholder** — not EVT-1 target |
| Hardware assumptions | Bluetooth LE, low-power Wi-Fi |

---

## API reference

```python
from gunnchos_device_os.device_classes import (
    list_device_classes,
    get_device_class,
    validate_device_class,
)

# All four EVT-1 alpha classes
list_device_classes()
# → ['student_14_5', 'handheld_hybrid', 'ds_xl_coder', 'wearables_arena_set']

dc = get_device_class("student_14_5")
missing = validate_device_class("student_14_5")  # [] if complete
```

Required fields are enforced in `REQUIRED_FIELDS` inside `device_classes.py`.

---

## Cross-links

| Document | Purpose |
|----------|---------|
| [HARDWARE_SOFTWARE_DEVICE_CLASS_CONTRACT.md](HARDWARE_SOFTWARE_DEVICE_CLASS_CONTRACT.md) | Field-by-field contract |
| [HARDWARE_SOFTWARE_CONTRACT.md](HARDWARE_SOFTWARE_CONTRACT.md) | Legacy EVT-1 summary |
| [DS_XL_DEPLOY_CONTRACT.md](DS_XL_DEPLOY_CONTRACT.md) | Deploy from ds_xl_coder |
| [MODES_OVERVIEW.md](MODES_OVERVIEW.md) | Mode policies per class |

---

## Validation

```bash
PYTHONPATH=. pytest -q tests/test_device_classes.py
```

---

## Limitations (alpha)

- No live HAL binding to battery, thermal, or dock detection
- Wearables class is a **placeholder** for future pilots
- Display and RAM values are **planning targets**, not manufacturing certification
- Launcher mock uses simplified device names in `deviceProfiles.ts` — map via `DEVICE_ID_MAP`
