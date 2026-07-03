# Reference Device Validation Report

**Do not claim physical hardware validation until this report is completed with real device test logs.**

## Report metadata

| Field | Value |
|-------|-------|
| Report ID | `REF-HW-YYYY-MM-DD-001` |
| Device SKU | `student_14_5` / `handheld_hybrid` / `ds_xl_coder` / `wearables_arena_set` |
| Device class | Reference target SKU |
| OS build | |
| Image / artifact | |
| Validation environment | `physical` / `vm` / `container` |
| Date | |
| Tester | |
| Host collector output | Path to JSON from `scripts/collect_reference_hardware_info.py` (optional) |

## Validation environment boundary

- [ ] **Physical device under test** — real GunnchOS target hardware present
- [ ] **VM only** — not sufficient for physical hardware claims
- [ ] **Container only** — not sufficient for physical hardware claims

> Set `physical_validation_performed: false` unless every hardware subsystem row was tested on the actual target device.

## Host snapshot (safe fields only)

Fill from `python3 scripts/collect_reference_hardware_info.py --output /tmp/host_snapshot.json` if helpful.
Do **not** include serial numbers, MAC addresses, or other private identifiers.

| Field | Value |
|-------|-------|
| OS | |
| Machine / arch | |
| CPU platform | |
| Python version | |
| Memory (GB, rounded) | |
| Root disk (GB, rounded) | |

## Subsystem checklist

| Area ID | Subsystem | Pass | Fail | N/A | Notes |
|---------|-----------|------|------|-----|-------|
| cpu_architecture | CPU architecture matches profile | | | | |
| ram | RAM meets minimum | | | | |
| storage | Storage class / capacity | | | | |
| display_resolution | Native resolution | | | | |
| touchscreen | Touch input | | | | |
| keyboard_mouse | Keyboard / mouse | | | | |
| controller_gamepad | Controller / gamepad | | | | |
| wifi | Wi-Fi connect | | | | |
| bluetooth | Bluetooth pair | | | | |
| audio_output | Speaker / headphone | | | | |
| microphone | Microphone capture | | | | |
| camera | Camera preview | | | | |
| usb_c_display | USB-C external display | | | | |
| battery | Battery / runtime sample | | | | |
| thermal_behavior | Thermal under load | | | | |
| sleep_wake | Sleep / wake cycle | | | | |
| suspend_resume | Suspend / resume | | | | |
| launcher_startup | GunnchOS launcher boots | | | | |
| local_workspace_persistence | Workspace survives restart | | | | |
| media_playback | Local non-DRM media plays | | | | |
| game_launch | Game Mode launches slice | | | | |
| accessibility_toggles | A11y settings persist | | | | |

## Software smoke (launcher)

| Check | Pass | Fail | Notes |
|-------|------|------|-------|
| Campus Mode first boot | | | |
| File manager CRUD | | | |
| Notes persist | | | |
| Settings persist | | | |
| Game Mode exit | | | |

## Sign-off

```yaml
physical_validation_performed: false
validation_environment: container
approved_for_beta_hardware_claim: false
container_only: true
```

- **physical_validation_performed:** `true` only if tested on real target hardware
- **validation_environment:** `physical` | `vm` | `container`
- **approved_for_beta_hardware_claim:** `true` only with Edmund sign-off and complete checklist
- **container_only:** `true` if no physical device was tested

## Evidence attachments

- [ ] Photos / screen recordings (no serial numbers in frame)
- [ ] Command logs
- [ ] `collect_reference_hardware_info.py` JSON output
- [ ] Link to OS build artifact manifest
