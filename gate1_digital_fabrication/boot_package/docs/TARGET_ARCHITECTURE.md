# G1-C1 Boot — Target Architecture (Nonphysical)

## Selected primary target family
- Android handheld / compute companion via ADB (existing Gate1 path)
- Embedded Linux SBC class (secondary)
- nRF52840 ring companion (Edge I/O) — separate firmware tree

## Build system
- Android: gradle/AOSP device image hooks (device profiles)
- Linux: Yocto/Buildroot candidate profiles (documented)
- Ring: Make + gcc host reference; Zephyr/nRF Connect SDK target when SDK present

## Image generation / flash / recovery
Scripts under `scripts/` are non-destructive by default and refuse destructive ops without explicit env.
