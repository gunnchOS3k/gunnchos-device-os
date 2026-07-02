# GunnchOS Phase 2B — Browser/PWA Open Behavior

**Branch:** `phase2b-browser-pwa-open-behavior`  
**Issues:** OS-002

## Real after this PR

- `appLaunchService.ts` — launch types (`external_url`, `internal_route`, `local_app`, `unavailable`) and results (`launched`, `blocked_by_policy`, `missing_url`, `unsupported`)
- Browser/PWA hub opens real URLs via `window.open` in a new tab
- Policy-aware blocking for School/Guardian (e.g. VS Code Web, ChatGPT)
- Launch result feedback in hub UI

## Still prototype

- No embedded browser shell or iframe
- No PWA install hook
- No production webview sandbox
- Google Workspace / D2L / etc. open in external browser tab only

## Mocks retired

- Browser/PWA **mock frame** removed from `BrowserPwaHub.tsx`
- "Phase 0 mock — no live iframe" copy removed

## Validation

```bash
make validate-full
```

## Manual test

1. Campus → Browser & PWA Hub
2. Click Google Drive → new tab opens (or launch result + fallback link)
3. Switch to School context → VS Code Web shows blocked message
4. Confirm claim: "external browser route prototype"
