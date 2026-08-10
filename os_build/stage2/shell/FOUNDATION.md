# gunnchShell Stage 2 Foundation

**Compositor:** Weston (Phase XII CI/host baseline retained)

## Decision

Stage 2 keeps **Weston** as the compositor foundation for digital validation and
CI. gunnchShell is the adaptive shell *above* Weston — one shell that switches
profiles rather than shipping separate OSes per device form factor.

## Why Weston

- Already integrated in Phase XII execution-reality CI (`weston` + `xvfb`)
- Wayland-native path suitable for desktop, tablet, and docked handheld
- Avoids inventing a compositor while OS-BASE / update / recovery land

## Shell contract (Python API)

Package: `gunnchos_device_os/stage2/shell/`

Surfaces: launcher, window management, quick settings, notifications, media,
search, file/share actions, session, display topology, input modality, dock
state, device role, accessibility.

## Adaptive profiles

| Profile | Intent |
|---------|--------|
| STUDENT_DESKTOP | Keyboard/mouse desktop productivity |
| DSXL_DUAL_SCREEN | Dual-screen DS-XL workflows |
| HANDHELD_GAMEPAD | Undocked handheld + controller |
| HANDHELD_DOCKED | Handheld in dock → desktop-like |
| OFFICE_DOCKED | Docked productivity + external display |
| TOUCH_TABLET | Touch-first tablet chrome |

## Claim boundary

- Digital shell contract + profile transitions validated in tests
- Does **not** claim GUNNCHOS_FRONTIER_OS_PARITY
- PHYSICAL_EXECUTION_FREEZE remains ACTIVE
