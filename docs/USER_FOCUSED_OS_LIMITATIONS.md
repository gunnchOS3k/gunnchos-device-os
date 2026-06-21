# User-Focused OS Limitations

**Status:** honest boundaries for the user-focused OS experience layer  

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

This document states what the repo **does not** provide today. For allowed language, see `product/CLAIM_BOUNDARY.md`.

---

## 1. Not a shipping operating system

| Limitation | Detail |
|------------|--------|
| No bootable OS image | Software layer + mock launcher only |
| No kernel / driver stack | hardware_abstraction.py is stub |
| No app store or package manager | launch_app returns mock: true |
| No certified secure boot | Planning docs only |

---

## 2. Mock and placeholder components

| Component | Limitation |
|-----------|------------|
| Guardian controls | mock: true — not production MDM |
| Creative apps | sketch_placeholder, write_placeholder, music_notes_placeholder |
| Switch access / voice input | Documented placeholders only |
| Sync / conflict resolution | Placeholder merge strategy |
| Collaboration share links | Placeholder strings |
| Remote wipe | Edge case doc only |
| Fleet admin UI | fleet_view_placeholder |

---

## 3. Dual systems not fully unified

| Limitation | Impact |
|------------|--------|
| EVT modes vs journey presets | Two APIs; mapping manual |
| EVT profiles (8) vs personas (22) | Demos use both |
| Two app registries | gunnchos_device_os vs gunnchos_launcher |

Contributors must know which layer they extend.

---

## 4. Platform and integration limits

| Limitation | Detail |
|------------|--------|
| Steam | steam_unavailable edge case; no compatibility guarantee |
| WSL | wsl_unavailable edge case; Windows-first strategy doc only |
| Netflix / Hulu / YouTube | Browser route labels; no proprietary apps |
| DRM | No circumvention; HDCP required for protected media |
| Real telemetry backend | Consent stubs only |
| i18n | English-first; no localization framework |

---

## 5. Accessibility limits

| Limitation | Detail |
|------------|--------|
| WCAG certification | Design intent only |
| Assistive technology testing | Not performed |
| Launcher mock a11y | Partial theme support |
| Automated a11y CI | Not present |

---

## 6. Evidence and validation limits

| Limitation | Detail |
|------------|--------|
| User testing | No IRB studies documented |
| Field deployment | No partner MOU or deployment reports |
| User-focused pytest | No dedicated test file |
| CI scope | EVT demo in CI; user-focused demo not in CI |
| Synthetic JSON | results/* labeled synthetic, not field data |

---

## 7. Audience-specific gaps

| Audience | Gap |
|----------|-----|
| Pre-K / children | No real touch-optimized app binaries |
| Guardians | No PIN/biometric implementation |
| Non-technical users | Onboarding not in launcher mock |
| Artists / writers / musicians | No real creative binaries |
| Advanced researchers | Bridges are stubs; not field-deployed |
| Accessibility-first | No AT co-design documented |

Full audit: [USER_FOCUSED_OS_AUDIT.md](USER_FOCUSED_OS_AUDIT.md).

---

## 8. Legal and compliance

**Not claimed:**

- COPPA / GDPR-K certification
- FERPA compliance review for school mode
- FCC / CE / UL hardware certification
- Production privacy impact assessment

Youth safety is **mock defaults** for research prototyping.

---

## 9. What this repo is good for

- Defining UX contracts for a future gunnchOS shell
- Data-driven personas, presets, packs, workspaces
- Policy and edge-case modeling
- CI smoke tests and synthetic demos
- Honest research spine integration (Edge-IO, 7GC, WAIKE, gunnchAI)

---

## 10. Path to reducing limitations

Prioritized from audit (documentation only):

1. Wire user-focused demo + validator into CI
2. Add pytest for persona/preset/onboarding chains
3. Ship one real offline app per creator mode
4. Unify preset routes in launcher mock
5. IRB-scoped usability study for Scooter + guardian flows
6. Third-party accessibility audit when UI stabilizes

See [USER_TESTING_PLAN.md](USER_TESTING_PLAN.md) and [CLAIMS_TO_EVIDENCE_USER_EXPERIENCE.md](CLAIMS_TO_EVIDENCE_USER_EXPERIENCE.md).

---

## 11. Required disclaimer

Every public summary must include:

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.
