# Claims to Evidence — User Experience

**Status:** living matrix for user-focused OS UX claims  

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

Repo-wide evidence: `quality/CLAIMS_TO_EVIDENCE_MATRIX.md`. Claim language rules: `product/CLAIM_BOUNDARY.md`.

**Status key:** `Supported (smoke)` = code/config/demo exists; `Partial` = stub or doc only; `Open` = not evidenced; `Forbidden` = do not claim without new evidence.

---

## UX claims matrix

| Claim | Evidence today | Test / validator | Status | Gap |
|-------|----------------|------------------|--------|-----|
| User-focused OS experience layer exists | `gunnchos_device_os/` 21+ modules, `product/USER_FOCUSED_OS_PRD.md` | `scripts/validate_user_focused_os.py` | Supported (smoke) | Not in CI |
| 22 personas with onboarding routes | `config/personas.yaml`, `persona_engine.py`, `onboarding_wizard.py` | validate_user_focused_os | Supported (smoke) | No user validation |
| 12 journey presets (Scooter → Spaceship + special) | `config/journey_presets.yaml`, `journey_preset_engine.py` | validate_user_focused_os | Supported (smoke) | Launcher mock partial |
| Scooter-to-spaceship principle documented | PRD, SCOOTER_TO_SPACESHIP_MODEL.md | Manual review | Supported (smoke) | Metaphor not user-tested |
| Customization (theme, layout, import/export) | `customization_engine.py`, `themes.yaml` | Manual / future pytest | Partial | UI rendering limited |
| 16 accessibility features configurable | `accessibility_manager.py`, `accessibility_defaults.yaml` | validate_coverage() | Supported (smoke) | No AT testing |
| Accessibility-first UX | Product + docs ACCESSIBILITY_AND_INCLUSION | — | Partial | Not WCAG certified |
| WCAG 2.1 AA conformant | — | — | Forbidden | Needs third-party audit |
| UDL-aligned design intent | UDL_ALIGNMENT.md, product ACCESSIBILITY_REQUIREMENTS | — | Supported (smoke) | Not classroom efficacy study |
| Guardian controls for youth | `guardian_controls.py` (mock: true) | Demo scenario | Partial | Not production MDM |
| No private content inspection by default | guardian_controls policy field | Code review | Supported (smoke) | Not legally reviewed |
| Offline-first learning mode | `offline_mode_manager.py`, offline preset | Demo scenario | Partial | Sync placeholder |
| Creator workflows (art/write/music) | `creator_mode_manager.py` | run_user_focused_os_demo | Partial | Placeholder apps only |
| App packs with beginner descriptions | `config/app_packs.yaml` | validate_user_focused_os | Supported (smoke) | No user readability test |
| Workspaces with quick_actions | `config/workspaces.yaml` | validate_user_focused_os | Supported (smoke) | Mock UI layouts |
| Seven-question onboarding | `onboarding_wizard.py` | Demo onboarding_sample | Supported (smoke) | Not in launcher mock |
| Edge cases with safe fallbacks | `edge_case_policy.py`, 24 cases in yaml | Manual | Supported (smoke) | Fallbacks not user-tested |
| Pre-K through postdoc coverage | PERSONA_MATRIX, PREK_TO_POSTDOC_USE_CASES | validate personas set | Supported (smoke) | Success moments not measured |
| Non-technical user can start simply | Scooter preset spec | — | Partial | No usability study |
| Privacy-safe telemetry default | `telemetry_consent.py`, tests | test_telemetry_consent | Partial | No production pipeline |
| User-tested UX | — | USER_TESTING_PLAN | Open | IRB study required |
| Finished / shipping OS | — | — | Forbidden | Explicit non-claim |
| Production MDM / parental controls | — | — | Forbidden | Mock only |
| Steam compatibility guarantee | steam_unavailable edge case | — | Forbidden | Hardware test needed |
| WSL available on all devices | wsl_unavailable edge case | — | Forbidden | Windows device log needed |
| Professional creative suite | — | — | Forbidden | Placeholder apps |
| COPPA / GDPR-K certified youth product | — | — | Forbidden | Legal review needed |

---

## Demo and synthetic outputs

| Output | Label | Valid as evidence for |
|--------|-------|----------------------|
| `results/user_focused_os_demo_output.json` | Synthetic demo | Scenario plumbing, not deployment |
| `results/device_os_evt1_demo_output.json` | Synthetic demo | EVT CI smoke |
| Guardian audit_log | Placeholder | Not audit evidence |

---

## Validators

| Script | Checks | In CI? |
|--------|--------|--------|
| `scripts/validate_user_focused_os.py` | Personas, presets, packs, workspaces, demo JSON | No |
| `scripts/validate_configs.py` | YAML integrity | Yes (e2e) |
| `scripts/check_user_experience_files.py` | Forbidden claim patterns (planned) | No |
| `pytest tests/` | Module smoke | Yes |

---

## How to upgrade a claim

1. Implement feature beyond stub.
2. Add automated test or validator step.
3. Run user study task from USER_TESTING_PLAN (if UX claim).
4. Update this matrix with evidence link and date.
5. Ensure wording matches CLAIM_BOUNDARY allowed language.

---

## Related documents

- [USER_FOCUSED_OS_AUDIT.md](USER_FOCUSED_OS_AUDIT.md)
- [USER_FOCUSED_OS_LIMITATIONS.md](USER_FOCUSED_OS_LIMITATIONS.md)
- [USER_TESTING_PLAN.md](USER_TESTING_PLAN.md)
- `product/CLAIM_BOUNDARY.md`
