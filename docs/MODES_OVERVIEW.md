# Modes Overview

**Status:** device OS alpha · config-driven OS behavior profiles  
**Modules:** `gunnchos_device_os/mode_manager.py`, `gunnchos_device_os/mode_policy.py`  
**Config:** `config/modes.yaml`

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## What is a mode?

A **mode** is a named policy bundle that controls:

- Allowed and blocked apps
- Telemetry category
- Network posture (filtered, standard, offline)
- Update policy
- Child safety tier
- Performance profile
- Mode-specific flags (WSL path, edge-io integration, focus mode, etc.)

Modes are loaded from YAML and queried via `get_mode_policy(mode)`. They are **not kernel-enforced** in alpha — the launcher mock and Python demos illustrate policy only.

---

## Mode catalog (12 modes)

| Mode | Primary use | Telemetry | Network |
|------|-------------|-----------|---------|
| **School** | Classroom learning | aggregated_opt_in | filtered |
| **Developer** | Coding, WSL, git | aggregated_opt_in | standard |
| **Coder** | CS student coding | aggregated_opt_in | standard |
| **Research Measurement** | Field measurement + Edge-IO | research_opt_in_only | standard |
| **Play** | Gaming | minimal | standard |
| **Media** | Streaming (browser routes) | minimal | standard |
| **Studio** | Creative writing/sketch | local_diagnostics | standard |
| **Workshop** | Maker + hardware lab | aggregated_opt_in | standard |
| **Laboratory** | Research notebooks | research_opt_in_only | standard |
| **Guardian** | Youth-safe restricted | none | filtered |
| **Library** | Shared public access | none | filtered |
| **Offline** | No network | none | offline_only |
| **Admin** | Fleet admin override | audit_only | standard |

---

## Featured modes (issue #5)

Detailed docs:

- [SCHOOL_MODE.md](SCHOOL_MODE.md)
- [DEVELOPER_MODE.md](DEVELOPER_MODE.md)
- [RESEARCH_MEASUREMENT_MODE.md](RESEARCH_MEASUREMENT_MODE.md)

Transition rules: [MODE_TRANSITION_RULES.md](MODE_TRANSITION_RULES.md)  
Full matrix: [MODE_POLICY_MATRIX.md](MODE_POLICY_MATRIX.md)

---

## API

```python
from gunnchos_device_os.mode_manager import list_modes, get_mode_policy

list_modes()  # tuple of 12+ mode names
get_mode_policy("School")  # dict with allowed_apps, blocked_apps, ...
```

```python
from gunnchos_device_os.mode_policy import can_transition

can_transition("School", "Developer", profile_type="child", guardian_approved=False)
# → allowed: False
```

---

## Device class support

Not every device class supports every mode — see [DEVICE_CLASSES.md](DEVICE_CLASSES.md).

---

## Launcher mock

Fleet view exposes a mode dropdown mapped via `MODE_ID_MAP` in `deviceProfiles.ts`.

---

## Validation

```bash
PYTHONPATH=. pytest tests/test_modes.py tests/test_mode_policy.py
python scripts/run_mode_policy_demo.py
```

---

## Claim boundary

Modes describe **intended behavior** for a shipping OS. Alpha implements YAML + transition checks only — not app sandbox enforcement.
