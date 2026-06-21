# gunnchOS Launcher Mock

**Status:** device OS alpha · Vite + React UX prototype  
**Not:** a shipping OS shell or installable launcher binary

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## What this app is

A **browser-based mock** of the gunnchOS launcher with two views:

- **Fleet view** — campus/device/mode research dashboard with synthetic telemetry and deploy panel
- **User-focused view** — persona-driven scooter-to-spaceship customization flow

Policy and validation live in the Python `gunnchos_device_os` package; this app illustrates UX contracts only.

---

## Quick start

```bash
cd apps/launcher_mock
npm install
npm run dev
```

Open the URL printed by Vite (typically `http://localhost:5173`).

Build static assets:

```bash
npm run build
npm run preview   # optional
```

---

## Project structure

```
apps/launcher_mock/
├── src/
│   ├── App.tsx              # Fleet + view routing
│   ├── main.tsx             # React mount
│   ├── deviceProfiles.ts    # Device/mode lists and ID maps
│   ├── appRegistry.ts       # Fleet app tiles
│   └── user-focused/        # User-focused experience (see README there)
├── index.html
├── package.json
└── vite.config.ts
```

---

## Views

| View | Enter | Purpose |
|------|-------|---------|
| Fleet (default) | Load app | Research operator demo |
| User-focused | "Your device (scooter → spaceship)" | Personalization demo |

Return via "Fleet view" fixed button in user-focused mode.

---

## Documentation

| Doc | Topic |
|-----|-------|
| [docs/LAUNCHER_MOCK_ARCHITECTURE.md](../../docs/LAUNCHER_MOCK_ARCHITECTURE.md) | Architecture |
| [docs/LAUNCHER_NAVIGATION_MODEL.md](../../docs/LAUNCHER_NAVIGATION_MODEL.md) | Navigation |
| [docs/LAUNCHER_ACCESSIBILITY_CONTRACT.md](../../docs/LAUNCHER_ACCESSIBILITY_CONTRACT.md) | Accessibility intent |
| [docs/LAUNCHER_COMPONENT_MAP.md](../../docs/LAUNCHER_COMPONENT_MAP.md) | Component inventory |
| [src/user-focused/README.md](src/user-focused/README.md) | User-focused modules |

---

## Tests

```bash
# Python doc existence (from repo root)
PYTHONPATH=. pytest tests/test_launcher_architecture_docs.py

# JavaScript — placeholder in alpha
npm test   # echoes "No tests yet"
```

---

## Claim boundary

- Synthetic telemetry and fleet counts are **mock**
- Deploy button does not call `deploy_contract.py`
- Secure boot / TPM labels are **targets**, not verified on hardware

See [product/CLAIM_BOUNDARY.md](../../product/CLAIM_BOUNDARY.md).
