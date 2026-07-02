# OS-009: CI full test suite

**Priority:** P0 · **Release target:** Beta

## Problem

Frontend Vitest and Python pytest may not both be required gates; BETA_GATE listed launcher e2e as not_started.

## Why it matters

Regressions in shell or policy must block merge.

## Definition of done

- GitHub Actions required checks: `pytest`, `npm test`, `npm run build`
- Document commands in README

## Tests

- CI run on PR

## Evidence required

- Green CI badge/log on main

## Non-goals

- Playwright full e2e (Phase 2.5)
- Hardware CI farm

## Claim boundary

Smoke-level frontend tests. Not full UAT.
