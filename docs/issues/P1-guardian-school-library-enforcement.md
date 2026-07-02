# OS-015: Guardian/school/library enforcement

**Priority:** P1 · **Release target:** Field pilot

## Problem

Policy exists in Python/YAML; shell shows summaries but does not enforce launches.

## Why it matters

Schools and guardians require Netflix/Hulu blocks and login warnings.

## Definition of done

- Shell reads active deployment mode from profile
- Blocked apps hidden or show denial message
- Library mode login warning on browser open

## Tests

- Extend `test_media_policy.py` + Vitest school mode UI

## Evidence required

- Test log + demo video

## Non-goals

- Full MDM
- Network-level filtering

## Claim boundary

Shell-level enforcement only until OS-level controls exist.
