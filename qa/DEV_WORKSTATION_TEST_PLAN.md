# Developer Workstation Test Plan

**Version:** 1.0

---

## Purpose

Validate Developer/Coder mode paths: WSL dry-run, terminal, VS Code route, Git workflow, deploy to targets, Edge-IO consent.

---

## Setup

- Student 14.5 reference PC (or mock for alpha)
- DS-XL Coder profile for deploy tests
- `scripts/install_wsl_dev_environment.ps1` available
- Deploy targets from `config/deploy_targets.yaml`

---

## Personas covered

- CS student (Workshop)
- Researcher (Edge-IO measurement)
- High school student (intro coding)

---

## Device classes covered

- Student 14.5 — full WSL path
- DS-XL Coder — deploy source
- Handheld Hybrid — light templates only

---

## Test steps

| ID | Step |
|----|------|
| D-01 | Enter Developer mode — tools visible |
| D-02 | WSL setup dry-run (script syntax + doc steps) |
| D-03 | Launch terminal route (mock OK) |
| D-04 | Launch VS Code route with workspace folder |
| D-05 | Git clone template project (mock repo) |
| D-06 | Deploy web_app to student_14_5 target (mock transport) |
| D-07 | Edge-IO task — consent gate blocks without consent |
| D-08 | Rollback deploy per deploy rollback model |
| D-09 | School hours block dev tools (policy) |

---

## Expected results

- Dev tools reachable from Developer/Coder modes
- Deploy respects transport + guardian/school flags
- Edge-IO blocked without consent
- Policy blocks honored with clear message

---

## Evidence to collect

- WSL dry-run test log (RC backlog #19)
- Deploy contract pytest + demo JSON
- Edge-IO consent pytest
- Screenshot of blocked school-hours dev

---

## Pass/fail criteria

**Pass:** D-01–D-09 pass; deploy + consent pytest green.

**Fail:** Deploy without consent; school block bypass; WSL script fails dry-run validation.

---

## Known limitations

- WSL not executed in CI Linux runner — dry-run on Windows agent required
- Real Wi-Fi/USB transport not available — mock API only
