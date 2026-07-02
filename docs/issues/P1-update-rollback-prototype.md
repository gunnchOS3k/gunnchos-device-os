# OS-016: Update/rollback prototype

**Priority:** P1 · **Release target:** RC

## Problem

`updater.py` and `rollback.py` return mock responses.

## Why it matters

Safe updates required for any field deployment.

## Definition of done

- Dev-signed manifest apply on ref device or VM
- Rollback drill documented

## Tests

- `test_updater_rollback.py` extended with integration path

## Evidence required

- Rollback drill log

## Non-goals

- Production fleet OTA

## Claim boundary

Prototype only until production signing exists.
