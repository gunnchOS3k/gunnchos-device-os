# OS-008: Python→React bridge automation in CI

**Priority:** P0 · **Release target:** Beta

## Problem

`export_launcher_contract.py` must be run manually before build. React can drift from Python/YAML.

## Why it matters

Single source of truth for apps, media metadata, and mode policy.

## Definition of done

- CI runs export before `npm run build`
- Makefile `build-launcher` depends on export
- Drift fails CI if contract stale

## Tests

- CI green on clean checkout
- Test that contract JSON validates schema

## Evidence required

- CI workflow log

## Non-goals

- Live FastAPI bridge (future)
- Real-time policy push

## Claim boundary

Generated JSON bridge only. Not a production IPC service yet.
