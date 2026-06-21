# Developer Workstation Requirements

**Status:** mock integrations + documented WSL script · **not production-proven**

> Developer mode path for CS students and builders. Primary SKU: Student 14.5 and DS-XL Coder.

---

## Required paths

| Path | Requirement | Alpha evidence |
|------|-------------|----------------|
| WSL | Install/configure script for Student 14.5 | `scripts/install_wsl_dev_environment.ps1` documented |
| Terminal | Launch from Developer/Coder mode | `launcher.py` mock |
| VS Code | Launch route with workspace folder | `launcher.py` mock |
| Git / GitHub | Clone, commit, push guidance | **planned** |
| Local project folders | Sandboxed under user profile | Policy design |
| Package warnings | Warn on unverified dependencies | **planned** |
| Offline dev templates | Starter projects without network | Deploy offline bundle |
| Edge-IO dev | Consent-gated measurement tasks | `edge_io_contract.py` |
| Deploy to devices | DS-XL → targets per deploy contract | `deploy_contract.py` + demo |
| Rollback / sandbox | Revert deploy; isolated test profile | `docs/DEPLOY_ROLLBACK_MODEL.md` |

---

## Mode integration

- **Developer mode** and **Coder mode** (DS-XL) expose dev tools
- Mode policy may block network or installs for school hours
- Guardian approval for child profiles installing dev tools

---

## Device class coverage

| Class | Dev workstation scope |
|-------|----------------------|
| student_14_5 | Full WSL + VS Code path |
| ds_xl_coder | Primary deploy source; keyboard-first IDE layout |
| handheld_hybrid | Light coding templates; full WSL N/A |
| wearables_arena_set | Edge-IO micro tasks only |

---

## Evidence before RC

- WSL developer setup dry-run test (see QA plan)
- Deploy contract e2e on mock transport with signed bundle placeholder
- Mode policy tests for dev tool restrictions

---

## Claim boundary

Developer workstation **requirements** are specified. WSL/VS Code routes are mocks — not a certified dev environment or finished shipping OS developer stack.
