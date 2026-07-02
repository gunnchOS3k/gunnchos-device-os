# OS-018: DRM/service certification research

**Priority:** P2 · **Release target:** GA (if pursued)

## Problem

Netflix/Hulu require DRM/CDM/HDCP; GunnchOS uses honest browser-route prototypes only.

## Why it matters

Streaming matters for student device but certification is legally/technically complex.

## Definition of done

- Research doc: Widevine path on Linux, HDCP external display, service policies
- Decision: pursue certification vs browser-only vs not supported

## Tests

- N/A (research)

## Evidence required

- `docs/DRM_CERTIFICATION_RESEARCH.md` with no circumvention paths

## Non-goals

- DRM circumvention
- False certification claims in alpha/beta

## Claim boundary

**No DRM circumvention. No official certification until partner/legal sign-off.**
