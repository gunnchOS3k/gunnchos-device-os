# OS-005: Real Game Mode launch adapter

**Priority:** P0 · **Release target:** Beta

## Problem

Game Mode "Launch (mock)" does not start any executable or web game.

## Why it matters

Game Mode must feel like a console; beta requires one real launch path.

## Definition of done

- `launchGame(id)` adapter: config maps game id → URL or binary path
- Exit game returns to library without shell crash
- Performance profile toggle preserved

## Tests

- Launch adapter unit test
- Mode switch Vitest after launch/exit

## Evidence required

- Launch log + screenshot

## Non-goals

- Steam integration for beta
- Online multiplayer

## Claim boundary

First-party games only for beta minimum. No Steam certification claim.
