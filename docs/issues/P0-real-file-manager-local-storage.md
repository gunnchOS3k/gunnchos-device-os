# OS-003: Real file manager and local storage

**Priority:** P0 · **Release target:** Beta

## Problem

`FileManagerMock.tsx` uses static `MOCK_FILES`. No real filesystem access.

## Why it matters

Students need Downloads, offline docs, code projects, and USB access.

## Definition of done

- List/create/rename/delete in scoped directory (Downloads)
- USB mount shown when available (Linux path)
- Retire mock file tree

## Tests

- CRUD integration test
- Permission denied for paths outside scope

## Evidence required

- Test log + screenshot of real files

## Non-goals

- Full desktop file manager parity
- Root filesystem access

## Claim boundary

Scoped student storage only. Not a general-purpose unconstrained FS browser.
