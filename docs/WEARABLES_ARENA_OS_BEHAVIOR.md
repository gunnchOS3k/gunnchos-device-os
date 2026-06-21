# Wearables / Arena Set OS Behavior

**Device ID:** `wearables_arena_set`  
**Hardware repo key:** `wearables_arena_set`  
**Status:** future-target placeholder · **physical validation not_started**

---

## Form factor and role

Wearables and supervised arena kit placeholder. Smallest mechanical bbox in hardware JSON. Deploy role: **future_target_placeholder**.

Profile: `hardware_compat/device_profiles/wearables_arena_set.yaml`

---

## Hardware assumptions (profile mirror)

| Subsystem | Assumption |
|-----------|------------|
| Display | Wearable or arena size class; variable resolution |
| Input | Touch, controller, gesture; voice placeholder |
| Audio | Speakers, haptic |
| Camera / mic | No webcam; arena marshal mic only |
| Storage | eMMC, minimum 64 GB |
| Memory | 4 GB RAM |
| Battery | Wearable short cycle |
| Thermal | Strict throttle, arena_safe policy |
| Ports | USB-C charge only |
| Dock | Not supported |

---

## Supported modes

Play, School, Offline, Library, Admin.

**Blocked:** Developer, Workshop (full workstation), unrestricted developer, spaceship preset without marshal.

Compatibility engine enforces blockers in `hardware_compatibility_engine.py`.

---

## Journey presets

scooter, bicycle, arcade, guardian, offline

**Blocked:** spaceship without marshal controls.

---

## App packs

learn_pack, game_pack, accessibility_essentials_pack, offline_essentials_pack

---

## Feature paths

| Feature area | Enabled | Notes |
|--------------|---------|-------|
| WSL / unrestricted developer | **no** | Hard blocked |
| Venue arcade | yes | Marshal controls required in Play/Arcade |
| Haptic learning | yes | |
| Supervised school session | yes | |
| Guardian marshal mode | yes | Child supervision required |
| Offline arena games / lessons | yes | |

---

## OS behavior highlights

1. **Marshal-first play** — Play and Arcade modes warn or require `marshal_control` in venue settings.
2. **Accessibility via haptic/audio** — Simplified language, audio cues, haptic cues defaults.
3. **Strict thermal** — `arena_safe` throttle limits sustained compute for safety and battery.
4. **No dock / no external display** — Kiosk and arena-local UX only.
5. **Fallbacks** — Blocked developer paths fall back to `marshal_controlled_arcade` or `arcade`.

---

## Engine blockers (summary)

| Combination | Message / fallback |
|-------------|-------------------|
| Developer mode | WSL workstation not supported |
| Workshop mode | Full developer workshop not supported |
| spaceship preset | Not allowed without marshal controls → arcade |
| Play/Arcade without marshal | Warning in venue settings |

---

## Known gaps

- `arena_safety_rules_not_field_validated`
- `no_wsl_workstation`

---

## Hardware repo references

- `../gunnchos-hardware-industrial-design/mechanical_correctness/device_mechanical_targets.json#wearables_arena_set`
- `../gunnchos-hardware-industrial-design/schematics/wearables_arena/`
- `../gunnchos-hardware-industrial-design/results/manufacturing/wearables_arena_set_package_index.md`

---

## Claim boundary

Lowest maturity SKU. Profile mirror only — arena safety, haptic hardware, and field deployment **not validated**.
