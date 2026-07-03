# Shippable OS Requirements

**Status:** target definition · user-focused OS alpha exists · **not shipping yet**

> A shippable gunnchOS release is a versioned, installable OS or OS-layer package with proven update, recovery, privacy, accessibility validation, and hardware compatibility evidence. This document defines the full target. Release evidence is required before stage-specific claims. This document does not claim any forbidden release state without linked evidence.

---

## Full target definition

A shippable gunnchOS release must include:

| Capability | Requirement summary | Current alpha evidence |
|------------|---------------------|------------------------|
| Installable OS or OS-layer package | Signed installer, version manifest, checksums | Installable bundle prototype (Phase 4B); not bootable ISO |
| First-run onboarding | Persona/preset wizard, profile setup | Launcher mock + user-focused demo |
| Device-class detection | student_14_5, handheld_hybrid, ds_xl_coder, wearables_arena_set | `device_classes.py` + YAML |
| User profile setup | Profiles, journey presets, import/export design | Profile manager prototype |
| Journey presets | Scooter-to-spaceship model, 11+ personas | `results/user_focused_os_demo_output.json` |
| Accessibility settings | Keyboard, controller, touch, contrast, motion | Launcher accessibility contract docs |
| Guardian / school / library modes | Policy stubs, approval flows | `guardian_policy.py`, mode policies |
| App packs / workspaces | Registry schema, install/launch policy | Launcher mock routes |
| Steam / gaming path | Play mode launch route (mock) | `steam_integration.py` mock |
| Media / browser path | Media apps route (mock) | `media_apps.py` mock |
| WSL / developer path | Dev mode, terminal, VS Code route | `wsl_dev_tools.py`, install script doc |
| Creator tools path | Writer, artist, music workspaces | Launcher mock creator routes |
| Offline-first path | Offline bundles, library mode | Deploy offline bundle contract |
| Privacy / telemetry consent | Consent states, child defaults | `consent_policy.py`, pytest |
| Security event log | Local audit events | `security_event_log.py` |
| Update mechanism | Signed manifest, channels | `updater.py` mock |
| Rollback mechanism | Last known good version | `rollback.py` design |
| Recovery path | Safe mode, factory reset rules | Documented requirements only |
| Hardware compatibility matrix | Per-SKU gates | YAML contract; not physically proven |
| Release notes | Template + generation | Template in release_artifacts |
| Support docs | Repair, troubleshooting | Partial docs in `docs/` |
| QA evidence | Master + domain test plans | `qa/` package |
| Signed artifact plan | Signing + SBOM requirements | Requirements only |
| Security review plan | Checklist + threat model | `docs/THREAT_MODEL.md` partial |
| User acceptance testing | UAT plan + report template | `qa/USER_ACCEPTANCE_TEST_PLAN.md` |
| Claim boundary | Explicit allowed/forbidden language | `CLAIM_BOUNDARY.md` |

---

## Release stages matrix

| Stage | Required artifacts | Required tests | Required evidence | Allowed claims | Forbidden claims |
|-------|-------------------|----------------|-------------------|----------------|------------------|
| **alpha** | Python modules, YAML configs, launcher mock, demo scripts, pytest suite, architecture docs | Unit tests, demo JSON validation, config schema tests | CI green on demo generation + pytest; demo walkthroughs | User-focused OS alpha; config-driven policy framework; launcher mock prototype | Finished shipping OS; GA release; certified accessibility; secure boot complete; production MDM |
| **beta** | Alpha artifacts + internal installer prototype + version manifest draft + expanded e2e tests | Launcher e2e smoke, mode transition tests, deploy contract e2e (mock transport) | Signed internal build log; beta test report | Beta-quality preview on reference hardware (single SKU); known-issue list published | Production OS; hardware-validated release across all SKUs; official Steam/media certification |
| **release_candidate** | Signed installer/bundle, checksums, SBOM, recovery bundle, release notes, hardware compatibility report draft, accessibility report draft, security review checklist complete | Full regression suite, UAT scripts, guardian/school/library session tests, offline mode tests, accessibility manual pass | RC sign-off template filled; artifact manifest complete; no P0 blockers | Release candidate for field evaluation on approved device list; not for general public sale | GA release; production fleet management; accessibility certified on hardware; production MDM deployed |
| **ga_release** | RC artifacts + GA signing keys + support runbooks + published SBOM + final UAT report + accessibility validation report | GA regression on all supported SKUs; performance baselines; battery/thermal handoff complete | GA release gate passed; security review signed; claim boundary reviewed | Generally available gunnchOS release for supported hardware per compatibility matrix | Finished shipping OS image is complete on all future SKUs; secure boot complete on all devices without per-SKU evidence |
| **field_pilot** | GA artifacts + pilot enrollment manifest + guardian/school pilot configs + field support playbook | Pilot UAT on real classrooms/libraries; offline lesson sync; Edge-IO consent sessions | Pilot completion report; incident log; repair workflow exercised | Field pilot deployment on enrolled sites with support contract | Nationwide production rollout; COPPA/GDPR certification without legal review evidence |
| **production_release** | Production signing pipeline, fleet update channel, MDM integration (if claimed), production SBOM archive, repair parts catalog link | Production regression; staged rollout validation; rollback drill on fleet | Production release gate passed; 30-day rollback drill evidence; support SLA met | Production release on supported hardware with documented support and update policy | Accessibility certified and validated on hardware without report; production MDM deployed without integration evidence |

---

## Evidence hierarchy

1. **Automated** — pytest, validators, CI artifacts
2. **Manual QA** — test plans in `qa/` with signed reports
3. **Hardware** — per-SKU compatibility reports (not yet produced)
4. **Legal / compliance** — separate review; not implied by OS repo alone

---

## Validation

```bash
python scripts/validate_shippable_requirements.py
python scripts/validate_release_gates.py
python scripts/validate_release_artifacts.py
python scripts/validate_qa_package.py
```

---

## Claim boundary

This document defines requirements for a future shippable OS. It does **not** claim that gunnchos-device-os is already a finished shipping OS image or GA release.
