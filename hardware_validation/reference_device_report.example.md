# Reference Device Validation Report — Container Example

**This is a container-only example. It does NOT claim physical hardware validation.**

## Report metadata

| Field | Value |
|-------|-------|
| Report ID | `REF-HW-2026-07-02-CONTAINER-EXAMPLE` |
| Device SKU | `container_reference` |
| Device class | Container kiosk (CI / dev host) |
| OS build | `launcher_mock` + `os_build/image_prototype` |
| Image / artifact | `os_build/image_prototype/` kiosk package |
| Validation environment | `container` |
| Date | 2026-07-02 |
| Tester | CI onchOS CI / automated validation |
| Host collector output | Generated at validation time (safe fields only) |

## Validation environment boundary

- [ ] **Physical device under test** — not applicable
- [ ] **VM only** — not applicable
- [x] **Container only** — nginx kiosk launcher in container

> This report documents automated container checks only. No GunnchOS target SKU was physically tested.

## Host snapshot (safe fields only)

Collected via `scripts/collect_reference_hardware_info.py`. Values vary by CI runner; rounded / redacted.

| Field | Example value |
|-------|---------------|
| OS | Linux |
| Machine / arch | x86_64 |
| CPU platform | x86_64 (generic) |
| Python version | 3.11+ |
| Memory (GB, rounded) | rounded total GB |
| Root disk (GB, rounded) | rounded total GB |

## Subsystem checklist

Hardware subsystems are **not tested** in this container example.

| Area ID | Subsystem | Pass | Fail | N/A | Notes |
|---------|-----------|------|------|-----|-------|
| cpu_architecture | CPU architecture matches profile | | | ✓ | Container host — not target SKU |
| ram | RAM meets minimum | | | ✓ | Container host — not target SKU |
| storage | Storage class / capacity | | | ✓ | Container host — not target SKU |
| display_resolution | Native resolution | | | ✓ | Not applicable in headless CI |
| touchscreen | Touch input | | | ✓ | Not applicable |
| keyboard_mouse | Keyboard / mouse | | | ✓ | Not applicable |
| controller_gamepad | Controller / gamepad | | | ✓ | Not applicable |
| wifi | Wi-Fi connect | | | ✓ | Not applicable |
| bluetooth | Bluetooth pair | | | ✓ | Not applicable |
| audio_output | Speaker / headphone | | | ✓ | Not applicable |
| microphone | Microphone capture | | | ✓ | Not applicable |
| camera | Camera preview | | | ✓ | Not applicable |
| usb_c_display | USB-C external display | | | ✓ | Not applicable |
| battery | Battery / runtime sample | | | ✓ | Not applicable |
| thermal_behavior | Thermal under load | | | ✓ | Not applicable |
| sleep_wake | Sleep / wake cycle | | | ✓ | Not applicable |
| suspend_resume | Suspend / resume | | | ✓ | Not applicable |
| launcher_startup | GunnchOS launcher boots | ✓ | | | Kiosk package healthcheck |
| local_workspace_persistence | Workspace survives restart | ✓ | | | Browser localStorage in dev tests |
| media_playback | Local non-DRM media plays | ✓ | | | Vitest local media prototype |
| game_launch | Game Mode launches slice | ✓ | | | Anime Aggressors web slice |
| accessibility_toggles | A11y settings persist | ✓ | | | Shell settings prototype |

## Software smoke (launcher)

| Check | Pass | Fail | Notes |
|-------|------|------|-------|
| Campus Mode first boot | ✓ | | Vitest shell tests |
| File manager CRUD | ✓ | | Browser workspace prototype |
| Notes persist | ✓ | | localStorage prototype |
| Settings persist | ✓ | | Partial settings subset |
| Game Mode exit | ✓ | | Vitest mode switch |

## Sign-off

```yaml
physical_validation_performed: false
validation_environment: container
approved_for_beta_hardware_claim: false
container_only: true
```

- **physical_validation_performed:** `false` — no physical device tested
- **validation_environment:** `container`
- **approved_for_beta_hardware_claim:** `false`
- **container_only:** `true`

## Evidence attachments

- [x] `hardware_validation/CONTAINER_KIOSK_VALIDATION_LOG.md`
- [x] `tests/test_image_prototype.py` — kiosk package validation
- [x] `make validate-full` — launcher build + tests
- [ ] Physical device photos / logs — **not present**
