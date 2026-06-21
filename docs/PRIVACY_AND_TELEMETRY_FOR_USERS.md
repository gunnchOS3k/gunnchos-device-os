# Privacy and Telemetry for Users

**Status:** device OS alpha · privacy-preserving telemetry stubs — not production analytics  

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

This document explains privacy **from a user and guardian perspective**. Technical models: `docs/security/PRIVACY_MODEL.md`, `docs/07_PRIVACY_AND_TELEMETRY.md`.

---

## 1. What we collect (design intent)

| Data type | Default | User control |
|-----------|---------|--------------|
| App launch counts (aggregate) | Opt-in per mode | Telemetry consent screen |
| Research measurements | Opt-in only | Research Measurement mode |
| Tutor session content | **Not collected** | gunnchai tutor_session_start: pii_collection false |
| Private files / messages | **Not inspected** | Guardian policy default |
| Location | Not claimed | N/A in alpha |
| Advertising IDs | **None** | N/A |

**Today:** Stubs in `telemetry_consent.py`, `src/telemetry/privacy_filter.py` — no production pipeline.

---

## 2. Telemetry tiers by mode

From `mode_manager.MODE_POLICIES`:

| Mode / context | Telemetry tier | Plain language |
|----------------|----------------|----------------|
| School | aggregated_opt_in | "Help improve school mode? Only counts, not your files." |
| Developer / Coder | aggregated_opt_in | Same; no source code upload |
| Play / Media | minimal | Almost nothing; play time for guardian if youth |
| Research Measurement | research_opt_in_only | Explicit consent for research export |
| Admin | audit_only | Fleet security logs (deployment context) |
| Guardian youth | privacy_safe_telemetry | Guardian must consent for pre-K |

---

## 3. User consent flow (mock)

1. First launch or mode switch to research → consent prompt.
2. User chooses opt-in or decline.
3. `telemetry_consent.py` records choice (local stub).
4. Export via `seven_gc_export` / `privacy_filter` — aggregated fields only.

Test: `tests/test_telemetry_consent.py`, `tests/test_privacy_filter.py`.

**Not claimed:** GDPR lawful basis assessment or COPPA compliance certification.

---

## 4. Guardian and youth privacy

| Promise | Implementation intent |
|---------|----------------------|
| No reading child's essays by default | private_content_inspection: false |
| No social media monitoring | Not in scope |
| Screen time ≠ surveillance | Time limits without content scraping |
| Pre-K strict privacy | personas.yaml privacy_level: strict |

See [GUARDIAN_AND_YOUTH_SAFETY.md](GUARDIAN_AND_YOUTH_SAFETY.md).

---

## 5. Research users

Graduate/postdoc personas using Laboratory or Spaceship:

- Field measurement data stays local until explicit export.
- edge_io bridge exports privacy-filtered aggregates (stub).
- No private packet capture claimed.

---

## 6. Offline privacy

- Offline mode: no network calls.
- Sync queue (placeholder): encrypted before upload when online.
- Library guest: session reset removes local profile.

---

## 7. What users can do

| Action | Available today |
|--------|---------------|
| Decline telemetry | Consent stub |
| View privacy summary | Documented; UI placeholder |
| Export own profile | customization_engine.export_profile() |
| Reset to safe defaults | reset_to_safe_defaults() |
| Delete account / wipe device | remote wipe placeholder in edge cases |

---

## 8. What we do not do

- Sell user data (not applicable — no commercial pipeline).
- Bypass DRM for media (browser routes only).
- Install spyware or keyloggers.
- Force telemetry for basic Scooter use (guardian consent for youth).

Forbidden claims: see `product/CLAIM_BOUNDARY.md` §3.

---

## 9. Transparency artifacts

| Artifact | Purpose |
|----------|---------|
| shared_contracts/telemetry_contract.schema.json | Export shape |
| results/e2e/ | Smoke artifacts (synthetic) |
| quality/CLAIMS_TO_EVIDENCE_MATRIX.md | Repo-wide evidence |

User-focused matrix: [CLAIMS_TO_EVIDENCE_USER_EXPERIENCE.md](CLAIMS_TO_EVIDENCE_USER_EXPERIENCE.md).

---

## 10. Evidence and gaps

| Claim | Evidence | Gap |
|-------|----------|-----|
| Opt-in research telemetry | test_telemetry_consent | No production backend |
| Privacy filter | test_privacy_filter | Not field-audited |
| No PII in tutor mock | test_os_modules | Real tutor integration TBD |
| User-readable privacy doc | This file | Not legally reviewed |

---

## 11. Related documents

- [GUARDIAN_AND_YOUTH_SAFETY.md](GUARDIAN_AND_YOUTH_SAFETY.md)
- [OFFLINE_FIRST_USER_EXPERIENCE.md](OFFLINE_FIRST_USER_EXPERIENCE.md)
- `docs/security/PRIVACY_MODEL.md`
