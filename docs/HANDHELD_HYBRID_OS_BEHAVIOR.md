# Handheld Hybrid OS Behavior

**Device ID:** `handheld_hybrid`  
**Hardware repo key:** `handheld_hybrid`  
**Status:** profile documented · **physical validation not_started**

---

## Form factor and role

Portable handheld console, dockable to TV/display. Controller-first play with optional keyboard dock. Expected class: *portable handheld console* (hardware JSON).

Profile: `hardware_compat/device_profiles/handheld_hybrid.yaml`

---

## Hardware assumptions (profile mirror)

| Subsystem | Assumption |
|-----------|------------|
| Display | 8.4″, 1920×1200, touch |
| Input | Controller primary; touch secondary; keyboard via dock |
| Audio | Speakers, haptic |
| Camera / mic | No webcam; mic present |
| Storage | On-module **32 GB eMMC** (RM121-D8E32) + **microSD** expansion (WP-002 Outcome A) |
| Memory | 8 GB RAM (SoM LPDDR4X) |
| Battery | Portable extended class |
| Thermal | Active cooling, gaming_balanced throttle |
| Ports | USB-C, gamepad USB |
| Dock | USB-C DP Alt Mode, TV mode |

---

## Supported modes

School, Play, Media, Studio, Arcade, Guardian, Library, Offline.

Developer/Workshop available in limited form (`light_coding`) — not full WSL workstation.

---

## Journey presets

scooter, bicycle, arcade, car, studio, offline, library

---

## App packs

learn_pack, game_pack, music_pack, offline_essentials_pack

---

## Feature paths

| Feature area | Enabled | Notes |
|--------------|---------|-------|
| WSL | no | By profile design |
| Light coding | yes | Reduced developer surface |
| Steam / gaming | yes | **Not certified** — known gap |
| Controller-first UI | yes | HID gamepad assumed |
| Media browser | yes | |
| TV / dock mode | yes | Not electrically validated |
| Guardian play windows | yes | |
| Offline games / lessons | yes | |

---

## OS behavior highlights

1. **Controller navigation** — Accessibility defaults include controller navigation paths.
2. **Arcade and Play** — Primary personas; compatibility engine favors controller input policy.
3. **Dock/TV** — When docked, display policy shifts to external display path (simulated).
4. **Thermal** — Active cooling profile expects gaming loads; no DVT thermal logs linked.
5. **Marshal N/A** — Unlike wearables, no arena marshal requirement unless deployed in venue kit context.

---

## Engine notes

No wearables-style Developer blockers. Steam and battery gaps surface as warnings in compatibility reports, not hard blockers.

---

## Known gaps

- `steam_compatibility_not_certified`
- `battery_validation_pending`
- `microsd_physical_endurance_pending` (WP-002 digital policy only; E5 physical pending)

---

## Hardware repo references

- `../gunnchos-hardware-industrial-design/mechanical_correctness/device_mechanical_targets.json#handheld_hybrid`
- `../gunnchos-hardware-industrial-design/npi/phase_xv/handheld_storage_headroom/HANDHELD_STORAGE_POLICY.md`
- `../gunnchos-hardware-industrial-design/dvt/DVT_THERMAL_TEST_PLAN.md`
- `../gunnchos-hardware-industrial-design/dvt/DVT_DISPLAY_INPUT_TEST_PLAN.md`
- `../gunnchos-hardware-industrial-design/results/manufacturing/handheld_hybrid_package_index.md`

---

## Claim boundary

Profile mirror — not physical hardware validation. Steam compatibility, battery runtime, and microSD endurance are **not proven**. WP-002 Outcome A is digital E4 only.
