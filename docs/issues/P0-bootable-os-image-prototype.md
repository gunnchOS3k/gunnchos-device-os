# OS-001: Bootable OS image prototype

**Priority:** P0 · **Release target:** Beta

## Problem

GunnchOS runs as a browser shell in Docker/Vite. There is no bootable image for reference hardware.

## Why it matters

Students need a device that boots into GunnchOS, not a dev server. Beta requires an installable internal prototype.

## Definition of done

- Bootable image (Yocto container or image) boots on reference x86_64 or ARM64
- Shell autostarts in kiosk mode
- Documented flash/install procedure

## Tests

- Boot smoke test log
- Shell reachable within 60s of power-on

## Evidence required

- Image artifact in CI or release bucket
- Boot log from reference hardware or VM

## Non-goals

- Multi-SKU support
- Production signing
- Secure boot validation

## Claim boundary

Do not claim GA-ready or secure boot complete until evidence exists.
