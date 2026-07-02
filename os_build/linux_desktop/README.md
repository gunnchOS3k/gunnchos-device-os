# GunnchOS Phase 0 — Linux Desktop Prototype

CI-testable Linux container that runs the GunnchOS shell in kiosk mode.

This is **not** a bootable OS image. It is the Phase 0 deliverable for "Linux base image" — a reproducible environment you can run on any x86_64/ARM64 host with Docker.

## Quick start

```bash
# From repo root
docker compose -f os_build/linux_desktop/docker-compose.yml up --build

# Open http://localhost:8080
```

## What's inside

- Debian Bookworm slim base
- Node.js 20 for building the launcher
- Python 3.11 for policy/onboarding scripts
- nginx serving the built GunnchOS shell
- Kiosk-style full-screen entry point

## Production path

Phase 0 → this container  
Phase 1+ → Yocto/meta-gunnchos layer (`os_build/yocto/`) for real ARM64 images  
Phase Beta → installable image per `requirements/INSTALLABLE_IMAGE_REQUIREMENTS.md`

## Build manually

```bash
cd os_build/linux_desktop
docker build -t gunnchos-phase0 .
docker run -p 8080:80 gunnchos-phase0
```
