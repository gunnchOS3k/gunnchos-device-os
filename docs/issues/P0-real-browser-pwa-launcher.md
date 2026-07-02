# OS-002: Real browser/PWA launcher

**Priority:** P0 · **Release target:** Beta

## Problem

Browser/PWA hub shows a mock frame and external links only. No embedded browser shell.

## Why it matters

School workflow requires Google Workspace, D2L, NotebookLM, GitHub, VS Code Web in a controlled browser.

## Definition of done

- URLs from `launcherContract.json` open in webview or system browser delegate
- PWA install path documented
- Mock frame removed or gated behind dev flag

## Tests

- E2E: open Google Docs URL loads content
- Vitest: hub no longer shows "mock frame" as only path

## Evidence required

- Screenshot/video of loaded web app
- Test log

## Non-goals

- Full Chrome extension support
- DRM-protected streaming certification

## Claim boundary

Browser route prototype only. No official service certification.
