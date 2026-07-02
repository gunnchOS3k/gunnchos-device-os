# OS-017: Hardware compatibility evidence

**Priority:** P1 · **Release target:** RC

## Problem

Hardware compat is simulated/profile-based only.

## Why it matters

Handheld target requires real driver, thermal, battery, display tests.

## Definition of done

- Physical test report per reference SKU
- Boot readiness not `"simulated"`

## Tests

- HW test suite on EVT board

## Evidence required

- Signed report in `hardware_release/` or linked repo

## Non-goals

- All SKUs for beta

## Claim boundary

Per-SKU evidence only. No fleet-wide claim without all reports.
