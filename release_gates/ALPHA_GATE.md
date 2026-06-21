# Alpha Gate

**Gate ID:** `alpha` · **Status:** `evidence_exists` (partial `validated` for demo coverage)

---

## Purpose

Establish a reproducible OS alpha: config-driven policies, launcher mock, demos, and automated tests — without claiming installable image or GA.

---

## Required evidence

| Item | Evidence location | Status |
|------|-------------------|--------|
| Core Python modules | `gunnchos_device_os/` | evidence_exists |
| Device class config | `config/device_classes.yaml` | evidence_exists |
| Mode policies | `config/modes.yaml`, tests | evidence_exists |
| Launcher mock | `apps/launcher_mock/` | evidence_exists |
| Demo outputs | `results/*_demo_output.json` | evidence_exists |
| pytest suite | `tests/`, CI | evidence_exists |
| Architecture docs | `docs/` | evidence_exists |
| User-focused 11 scenarios | `results/user_focused_os_demo_output.json` | validated |

---

## Required tests

- `pytest -q tests/` green after demo generation
- Validators: `validate_user_focused_os.py`, `validate_issue_closure.py`, shippable package validators

---

## Allowed claims

- User-focused OS alpha
- Config-driven launcher/customization framework
- Issue backlog operational OS pass (issues #1, #2, #3, #5, #7, #8, #9, #10, #12)

---

## Forbidden claims

- Beta, RC, GA, or production release
- Installable image validated on hardware
- Finished shipping OS

---

## Exit to beta

See [BETA_GATE.md](BETA_GATE.md): internal installer prototype + launcher e2e smoke.

---

## Owner

OS team · Sign-off: [RELEASE_SIGNOFF_TEMPLATE.md](RELEASE_SIGNOFF_TEMPLATE.md)
