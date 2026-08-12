# gunnchOS Device Lab Interactive Development Guest v1

## Why this exists

The slim Alpine initramfs-only guest (`os_build/device_lab_guest/`, label
`DEVICE_LAB_DEVELOPMENT_GUEST`) boots a serial-console rootfs with no
compositor, no GUI apps, and no persistent root filesystem. It is sufficient
for boot-marker and service-supervision proofs, but it is **insufficient** to
ever earn:

- `LIVE_GUNNCHOS_VISUAL_PASS` (needs a real compositor/shell + app window on
  screen, not a blank/near-black framebuffer)
- `DSXL_DUAL_COMPOSITOR_UX_PASS` (needs two real compositor surfaces with
  window placement, focus move, and disconnect/reconnect/layout restore)
- `RING_TO_REAL_APP_STATE_MUTATION_PASS` (needs a real in-guest document
  editor / browser / game process that Ring input can mutate)

This directory adds the **gunnchOS Device Lab Interactive Development Guest**
(label `DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST=true`): a persistent-root-disk
Alpine guest with a real Wayland compositor (weston), a browser, a terminal
editor, audio, and input stack, intended to eventually host real apps for
in-guest LIVE / DS-XL / Ring proofs.

**This is scaffolding, not a finished build.** It is the *required path
forward* for LIVE/DSXL/Ring in-guest proofs (see
`artifacts/wp011r/DEVICE_LAB_REMAINING_DIGITAL_GAPS.json`), but no PASS token
is flipped by adding this scaffolding alone. Every PASS token stays `false`
until real boot + real captured evidence earns it.

## Claim boundary

- `DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST = true` — this is a **development
  guest**, exactly like the slim guest, just with a bigger userspace.
- `SHIPPING_IMAGE = false` — this guest is **never** shipped to a physical
  gunnchOS3k device. It exists only inside the Device Lab / QEMU.
- `DEVICE_LAB_DEVELOPMENT_GUEST` (the slim Alpine initramfs guest) remains
  unchanged and still exists at `os_build/device_lab_guest/`. This interactive
  guest does not replace it — it is a separate, additional guest image
  selected by an explicit environment flag.
- `SILICON_EXACT_EMULATION = false` always. `PRODUCTION_KEYS_USED = false`
  always. Nothing here claims physical boot, EVT hardware, or
  `PRODUCTION_READY`.
- No PASS token defined elsewhere (`LIVE_GUNNCHOS_VISUAL_PASS`,
  `DSXL_DUAL_COMPOSITOR_UX_PASS`, `RING_TO_REAL_APP_STATE_MUTATION_PASS`,
  `FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS`, `ECO010_SOAK_PASS`, or any master
  "complete" token) is set to `true` by this scaffolding.

## Architecture

```
                         host (QEMU launcher)
                              │
                              │ GUNNCH_LAB_INTERACTIVE_GUEST=1
                              ▼
                 ┌─────────────────────────────┐
                 │  QEMU -machine virt/q35      │
                 │  -device virtio-gpu-pci      │  <- GPU scanout for weston
                 │  -device virtio-keyboard-pci │  <- real key events
                 │  -device virtio-tablet-pci   │  <- absolute pointer events
                 │  -drive interactive-root.qcow2, if=virtio  <- persistent rootfs
                 │  -chardev socket (virtio-serial) org.gunnchos.guest_agent.0
                 └─────────────────────────────┘
                              │ virtio-serial (unix socket, host-local only)
                              ▼
                 ┌─────────────────────────────┐
                 │ guest: Alpine rootfs          │
                 │  - seatd + weston (Wayland)   │
                 │  - chromium (or firefox)      │
                 │  - terminal + editor           │
                 │  - pipewire/alsa audio         │
                 │  - libinput                     │
                 │  - godot (optional)             │
                 │  - gunnch-guest-agent           │
                 │    (framebuffer_capture,        │
                 │     compositor_info,            │
                 │     app_launch, + existing cmds)│
                 └─────────────────────────────┘
```

Root disk (`interactive-root-<arch>.qcow2`) is a **persistent** virtio-blk
disk, unlike the slim guest's ephemeral initramfs. This is required because a
real compositor + browser + editor stack does not fit (and should not live)
in an initramfs held entirely in guest RAM.

## Arch matrix

| Arch      | Host                                   | Accel        | Status |
|-----------|-----------------------------------------|--------------|--------|
| `aarch64` | macOS Apple Silicon (Mac HVF)            | `hvf` (native)| Primary dev target — matches slim guest's Alpine aarch64 base |
| `x86_64`  | Linux (Student / DS-XL physical profile)| `kvm` (native), `tcg` fallback | Required for parity with Student/DS-XL hardware profile emulation; build script not yet implemented (see below) |

Only the `aarch64` rootfs build script is implemented in this wave
(`scripts/build_interactive_rootfs_alpine_aarch64.sh`). The `x86_64` path is
documented in the manifest's `arch_matrix` but has no build script yet —
`interactive_image_builder.py` raises `NotImplementedError` honestly if asked
to build for `x86_64`.

## Required packages (declared, not yet all proven installed)

See `INTERACTIVE_GUEST_MANIFEST.json` (`required_packages`) for the
machine-readable list. Summary:

| Package | Role | Optional? |
|---|---|---|
| `weston` | Wayland reference compositor | no |
| `seatd` | seat management for weston (no logind in Alpine) | no |
| `mesa-dri-gallium` | software/virtio-gpu GL rendering | no |
| `foot` | Wayland terminal emulator | no |
| `chromium` | Wayland-capable browser (Ozone/Wayland) | no (preferred) |
| `firefox` | Browser fallback if `chromium` unavailable | fallback |
| `nano` | Terminal text editor | no |
| `pipewire` + `pipewire-alsa` | Audio server + ALSA compatibility shim | no |
| `alsa-utils` | ALSA fallback if pipewire unavailable | fallback |
| `libinput` | Input device handling for weston | no |
| `godot` | Game engine runtime, for FOUR_GAME real-runtime work | **yes** |

## How the full build actually runs

Building an aarch64 Alpine rootfs with real Wayland packages **cannot be done
by simply extracting `.apk` files on a non-Linux host.** Alpine packages
carry post-install trigger scripts (udev rules, `adduser`/`addgroup` calls,
GL ICD registration, etc.) that must actually **execute** inside a Linux
aarch64 (or emulated aarch64) userspace. Two supported real methods, in
priority order:

1. **Docker cross-build (preferred on Apple Silicon Macs).** Docker Desktop on
   Apple Silicon runs a native `linux/arm64` VM, so
   `docker run --rm --platform linux/arm64 -v $ROOTFS:/target alpine:3.21 sh -c
   'apk update && apk add --root /target --initdb -U weston seatd ...'`
   executes real aarch64 package scripts natively (no QEMU user-mode
   emulation needed). This is the method
   `build_interactive_rootfs_alpine_aarch64.sh` attempts first.
2. **Linux host with `binfmt_misc` + `qemu-user-static`.** A Linux host (or CI
   runner) with `qemu-aarch64-static` registered in `binfmt_misc` can `chroot`
   into the extracted rootfs and run `apk add` with full script execution,
   even from an `x86_64` host. This is the fallback method the script
   attempts if Docker is unavailable.
3. **Neither available (this Mac, right now):** the script downloads the real
   Alpine minirootfs tarball (genuine network fetch, real bytes, real
   sha256), but **refuses to fake a full package install** and **exits
   non-zero** with an honest message naming the missing capability. It does
   **not** claim any boot or GUI evidence in this case.

Regardless of which build path executes, the resulting rootfs is packed onto
the persistent `interactive-root-<arch>.qcow2` disk created (and, when tools
allow, formatted) by
`gunnchos_device_os/device_lab/interactive_image_builder.py`. A qcow2 file
with no filesystem written to it is recorded as `disk_formatted: false` and
is honestly a placeholder — it is not claimed as a bootable rootfs.

## Guest agent protocol additions

The existing `gunnchos.guest_agent.v1` protocol (virtio-serial JSON-lines,
see `gunnchos_device_os/device_lab/guest_agent/PROTOCOL.md`) gains three
commands needed to prove interactive-guest state honestly:

- `framebuffer_capture` — request a raw framebuffer/DRM capture from the
  guest compositor. Distinct from the existing QEMU-monitor `screendump`
  path: this one is guest-side (proves the *guest* rendered something, not
  just that QEMU's virtual scanout memory is non-zero).
- `compositor_info` — ask the guest agent whether a compositor (weston) is
  actually running, which seat/socket it owns, and how many outputs/surfaces
  it has. Used to reject "DRM connector enumerated" as a false proxy for
  "compositor surface exists" (see `virtualization/dsxl_outputs.py`).
- `app_launch` — ask the guest agent to start a real in-guest application
  (browser, editor, game) by name/command and report the resulting PID and
  exit status. Used to replace host-side `http.server`/hybrid-surface proofs
  with genuine in-guest process launches for Ring/FOUR_GAME work.

The host-side mailbox stub (`GuestAgentClient._local_stub`) implements these
three commands **honestly as stubs**: they report `"stub": true` and
`"ok": false` (or `"available": false`) rather than fabricating captures,
compositor state, or launched PIDs. Only a real virtio-serial-connected guest
agent running inside a booted interactive guest can return real data for
these commands.

## QEMU wiring

Set `GUNNCH_LAB_INTERACTIVE_GUEST=1` (alias: `GUNNCHDEVICE_LAB_INTERACTIVE_GUEST=1`)
before starting a Lab QEMU session
(`gunnchos_device_os/device_lab/virtualization/qemu_guest.py`) to make the
launcher:

- resolve the interactive guest's persistent root disk
  (`interactive_guest_disk_path()`) instead of (in addition to) the slim
  guest's ephemeral `persist.qcow2`, and fail with a clear, honest error if
  that disk has not been created yet (via `interactive_image_builder`);
- attach `virtio-gpu-pci` (GPU scanout for a real compositor, not just the
  DS-XL dual-scanout path), `virtio-keyboard-pci`, and `virtio-tablet-pci`
  (real key + absolute-pointer input devices, not just QEMU monitor
  `sendkey`);
- set `gunnchos.interactive_guest=1` on the kernel command line so the guest
  init (once built) can distinguish this boot from the slim guest.

This wiring makes the interactive guest **recognized and selectable** by the
QEMU launcher. It does not, by itself, boot a working weston session — that
still requires the rootfs build described above to have actually populated
the root disk.

## What is real right now vs. what is still a stub

| Claim | Status |
|---|---|
| `INTERACTIVE_GUEST_MANIFEST.json` generation | **Real** — written by `interactive_image_builder.py` from the declared package/arch data below |
| qcow2 root disk file creation | **Real when `qemu-img` present** (it is, on this Mac); disk is an empty/placeholder image unless a real rootfs build has populated it |
| Alpine minirootfs download | **Real network fetch** when the build script runs with network access |
| weston/chromium/etc. package install with real scripts | **Not run on this Mac** — no Docker, no Linux chroot/binfmt available in this session (checked and recorded — see evidence below); script exits non-zero honestly rather than faking it |
| QEMU virtio-gpu/keyboard/tablet device recognition | **Real** — wired into `qemu_guest.py`, gated by `GUNNCH_LAB_INTERACTIVE_GUEST=1` |
| Guest boot with visible weston/app window | **Not attempted / not earned** — requires the rootfs build above |
| Any `*_PASS` or master-complete token | **`false`** — nothing here earns them |
