# gunnchos-device-os

**gunnchOS** — first-party OS for the gunnchOS3k device family (Student 14.5, Handheld Hybrid, DS-XL Coder) plus **gunnchDevice Lab** digital verification.

> **Current state:** digitally integrated / partially validated. **Not** a finished shipping OS. **Not** production-ready. Device Lab guest = `DEVICE_LAB_DEVELOPMENT_GUEST` (Alpine + gunnchOS-services overlay), not the shipping image. A second `DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST` guest (`os_build/device_lab_interactive_guest/`) is scaffolded as the required path for in-guest LIVE/DS-XL/Ring proofs — also `SHIPPING_IMAGE=false`, not yet built or booted.

Ecosystem portal: [gunnchos-research-portal](https://github.com/gunnchOS3k/gunnchos-research-portal) · Product charter: [field-kit charter](https://github.com/gunnchOS3k/gunnchos-7gc-ai-ran-field-kit/blob/main/program/charter/gunnchOS3k_PRODUCT_CHARTER.md)

Issue closure matrix: [docs/ISSUE_CLOSURE_MATRIX.md](docs/ISSUE_CLOSURE_MATRIX.md)

## What is this?

Operating system, Device Lab, continuity/fabric hooks, Ring/input paths, update/recovery, and Golden Journey digital evidence for first-party devices.

## Why does it exist?

So every first-party device runs one coherent gunnchOS stack with reproducible digital evidence before physical EVT claims.

## Where does it fit?

Layer 4 (gunnchOS) + Device Lab evidence in the Product Charter. Consumed by portal navigation; depends on hardware BOM truth.

## What is real today?

- Device Lab QEMU/HVF guest path (development guest)
- Profile sync from hardware truth (Student/DS-XL/Handheld)
- Golden Journey digital evidence (WP-003)
- Internal security red-team readiness (WP-007)
- Wave 4/5 Lab tokens as documented in the completion register (challenge depth in WP-011R)

## What is simulated / modelled?

- Ring spatial accuracy (`SIMULATED`)
- Performance prediction / twin correlation
- Some app surfaces in Lab behavioral mode

## What is physical / external pending?

- VF4/VF5/VF6, HIL, battery/thermal/RF
- Shipping OS image, certification, carrier acceptance
- ECO-010 full soak and four-game *production* Lab runtimes (WP-011R open)
- A booted Interactive Development Guest with a real compositor/apps (`os_build/device_lab_interactive_guest/` — manifest/script/QEMU-wiring scaffolded; rootfs package install not yet run anywhere; no boot attempted)

## Try / inspect in 5 minutes

```bash
# Launcher prototype (historical UI path — not shipping proof)
python3 scripts/export_launcher_contract.py
cd apps/launcher_mock && npm install && npm run dev
# → http://localhost:5173

# Device Lab score from register (not independent 10/10)
PYTHONPATH=.:src python3 scripts/device_lab_score_from_register.py
```

## Claim boundary

`SILICON_EXACT_EMULATION=false` · no PRODUCTION_READY · no CERTIFIED · Cursor opens DRAFT PRs only.

---

## HISTORICAL — Phase / beta train

Older “Phase 4 beta completion train” framing and phase docs live under `docs/` (e.g. `docs/BETA_STATUS_DASHBOARD.md`, `docs/PHASE0.md`). Treat as **HISTORICAL/LEGACY** relative to Cycle 3A current-state language above. `beta_ready` remains **false**.

## Operational status (honest)

**gunnchOS is not a finished shipping OS.**

| Category | Real today | Prototype today | Mock today | Missing for beta | Missing for GA |
|----------|------------|-----------------|------------|------------------|----------------|
| **Shell & modes** | First boot, Campus/Game/Media UI, Vitest smoke | Mode switching, dock | App launches, game launch | Policy enforcement in shell | Full a11y on hardware |
| **Policy** | Python modes, media metadata, contract export | Guardian/school in config | Shell enforcement | CI auto-export | Kernel enforcement |
| **Productivity** | PWA list, contract apps, **Files v1, Notes v1** | Settings subset persists | Browser frame | PDF, webview | Cloud sync |
| **Media** | DRM disclaimers, Media Mode UI | YouTube external link | Netflix/Hulu playback, local player | Local video, webview YouTube | Service certification |
| **Games** | Game metadata, Game Mode UI | — | Launch (mock) | One real game build | Three vertical slices |
| **Platform** | Docker prototype, SBOM scripts | HW compat (simulated) | Updater, rollback | Installable image | Production OTA |

Full matrix: [docs/FULL_OPERATIONAL_GAP_MATRIX.md](docs/FULL_OPERATIONAL_GAP_MATRIX.md) · Mocks: [docs/MOCK_RETIREMENT_PLAN.md](docs/MOCK_RETIREMENT_PLAN.md) · Beta gate: [docs/BETA_RELEASE_GATE.md](docs/BETA_RELEASE_GATE.md) · **Beta status:** [docs/BETA_STATUS_DASHBOARD.md](docs/BETA_STATUS_DASHBOARD.md)

## Start here

- [gunnchos_device_os/device_lab/README.md](gunnchos_device_os/device_lab/README.md) — Device Lab
- [docs/USER_FOCUSED_OS_ARCHITECTURE.md](docs/USER_FOCUSED_OS_ARCHITECTURE.md)
- [docs/DEVICE_CLASSES.md](docs/DEVICE_CLASSES.md)
- [docs/MODES_OVERVIEW.md](docs/MODES_OVERVIEW.md)
- [GUNNCHOS_REQUIREMENTS_v0.1.md](GUNNCHOS_REQUIREMENTS_v0.1.md)

## Tests

```bash
make validate-full
# or: pytest -q && cd apps/launcher_mock && npm test
PYTHONPATH=.:src pytest -q tests/device_lab/test_wp011r_tokens.py
```

## Evidence

- `artifacts/wp011r/` — WP-011R gaps, independent score, acceptance matrix
- Golden Journey scorecards / WP-007 artifacts under `artifacts/`
