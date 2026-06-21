# Hardware Input and Display Policy

**Status:** implemented in software · **not hardware-validated**

**Code:** `gunnchos_device_os/hardware_input_policy.py`, `gunnchos_device_os/hardware_display_policy.py`  
**Hardware references:** `../gunnchos-hardware-industrial-design/dvt/DVT_DISPLAY_INPUT_TEST_PLAN.md`, `mechanical_correctness/DISPLAY_FIT_CHECK_PLAN.md`

---

## Purpose

Govern input modality availability and display routing (built-in, touch, external, dual-screen, dock) per device profile.

---

## Input policy dimensions

| Dimension | Check |
|-----------|-------|
| Keyboard | built-in, dock_optional, or absent |
| Touch | single or dual-screen touch |
| Stylus | supported or not |
| Controller | HID gamepad, arena controls |
| Gesture / voice | placeholder flags on wearables |
| Accessibility | screen reader labels, keyboard/controller navigation |

---

## Per-class input summary

| Input | Student 14.5 | Handheld | DS-XL | Wearables |
|-------|:------------:|:--------:|:-----:|:---------:|
| Built-in keyboard | ✓ | dock opt | ✓ | ✗ |
| Touch | ✓ | ✓ | dual | ✓ |
| Stylus | ✓ | ✗ | ✗ | ✗ |
| Controller | ✗ | ✓ primary | ✗ | ✓ |
| Controller nav a11y | — | ✓ | — | — |

Handheld: controller-first UX; keyboard only when docked.  
DS-XL: keyboard-first with dual-screen touch workflow.  
Wearables: touch + controller + gesture; no keyboard.

---

## Display policy dimensions

| Dimension | Check |
|-----------|-------|
| Resolution / size | from profile `display` block |
| Touch | boolean |
| Dual screen | DS-XL only |
| External display | dock USB-C DP Alt Mode |
| TV mode | Handheld dock flag |
| Wearable size class | variable resolution |

---

## Per-class display summary

| Display | Student 14.5 | Handheld | DS-XL | Wearables |
|---------|:------------:|:--------:|:-----:|:---------:|
| Primary | 14.5″ 1920×1200 | 8.4″ 1920×1200 | 7″ dual 1280×720 | variable |
| External | ✓ dock | ✓ TV/dock | ✓ deploy | ✗ |
| Dual-screen OS shell | ✗ | ✗ | ✓ (unproven HW) | ✗ |

---

## Dock and external display

When `dock.supported` and `usb_c_dp_alt_mode`:

- OS may route primary UI to external display (policy simulation).
- Student and Handheld: classroom and TV scenarios.
- DS-XL: deploy source may mirror for demo.

**Not validated:** electrical DP Alt Mode, EDID, hotplug on reference hardware.

Hardware contract: `../gunnchos-hardware-industrial-design/docs/OS_HARDWARE_CONTRACT.md` (docking row).

---

## DVT alignment (planned)

Hardware repo test plan `dvt/DVT_DISPLAY_INPUT_TEST_PLAN.md` defines lab cases OS should eventually mirror:

- Panel init and rotation
- Touch calibration and palm rejection
- Keyboard matrix / dock hotplug
- Controller mapping and rumble (Handheld)
- Dual-display extended mode (DS-XL)

**Status:** plans exist; execution logs not linked.

---

## Failure and fallback behavior

| Condition | OS behavior (intended) |
|-----------|------------------------|
| Touch unavailable | Fall back to keyboard/controller where supported |
| External display fail | Remain on built-in; warn user |
| Controller missing on Handheld | Touch-first fallback; gaming warnings |
| Dual-screen init fail (DS-XL) | Single-screen degraded coder layout |

Degraded paths are **documented intent** — not proven on hardware.

---

## Related documents

- [HANDHELD_HYBRID_OS_BEHAVIOR.md](HANDHELD_HYBRID_OS_BEHAVIOR.md)
- [DS_XL_CODER_OS_BEHAVIOR.md](DS_XL_CODER_OS_BEHAVIOR.md)
- [HARDWARE_MODE_POLICY.md](HARDWARE_MODE_POLICY.md)
