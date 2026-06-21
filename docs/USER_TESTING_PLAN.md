# User Testing Plan

**Status:** planned protocol — no participant studies completed in this repo  

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

**Not claimed:** user-tested UX, WCAG certification, or validated persona matrix until studies listed below are completed and linked.

---

## 1. Objectives

1. Verify Scooter-to-Spaceship presets match real user mental models.
2. Validate onboarding comprehension for non-technical users and guardians.
3. Test accessibility settings with assistive technology users.
4. Measure creator workflow viability for artist/writer/musician personas.
5. Confirm offline-first flows reduce anxiety on unreliable networks.
6. Produce evidence rows for [CLAIMS_TO_EVIDENCE_USER_EXPERIENCE.md](CLAIMS_TO_EVIDENCE_USER_EXPERIENCE.md).

---

## 2. Study phases

| Phase | Method | Participants (target) | Duration | Deliverable |
|-------|--------|----------------------|----------|-------------|
| P0 — Heuristic review | Internal WCAG/UDL checklist | 2 reviewers | 1 week | Issue log |
| P1 — Moderated usability | Task-based sessions | 8–12 mixed ages | 2 weeks | Task success rates |
| P2 — Guardian dyads | Parent + child pairs | 6 dyads | 2 weeks | Safety flow notes |
| P3 — AT sessions | Screen reader, switch users | 4 participants | 2 weeks | AT compatibility report |
| P4 — Field pilot | School/library partner | 1 site, 20 devices | 4 weeks | Deployment memo |

All human-subjects work requires IRB or equivalent ethics approval before P1+.

---

## 3. Participant segments

| Segment | Recruitment criteria | Priority tasks |
|---------|---------------------|----------------|
| Pre-K / early reader | Ages 4–8 with caregiver | Scooter tap targets, letter activity |
| Middle / high school | Ages 11–17 | Bicycle/Car homework, mode switch |
| Non-technical adult | Self-rated low tech confidence | Onboarding, reset to simple |
| Guardian | Parent of youth user | Approve app, screen time, no surveillance trust |
| Artist / writer / musician | Self-identified creators | Studio workspace, offline save |
| Accessibility-first | Uses AT or a11y settings daily | Keyboard, contrast, simplified language |
| Low-bandwidth | Rural or metered connection | Offline preset, sync messaging |
| Researcher | Grad+ in STEM | Laboratory export consent |

---

## 4. Task scripts (P1)

### T1 — First run (all segments)

1. Complete seven-question onboarding on launcher mock (when available) or guided script.
2. Reach home screen.
3. **Success:** User can describe what device is "for" in their own words.
4. **Metric:** Time to first intentional app open; comprehension question score 1–5.

### T2 — Scooter simplicity (pre-K, overwhelmed, a11y)

1. Start in Scooter preset.
2. Open WAIKE Offline (or placeholder).
3. Find Help.
4. **Success:** No accidental navigation to blocked app.
5. **Metric:** Error count; caregiver assist required (Y/N).

### T3 — Guardian approval (guardian dyad)

1. Child requests blocked app.
2. Guardian approves from dashboard (mock UI).
3. **Success:** Child sees approved app; guardian confirms no private content viewed.
4. **Metric:** Trust rating 1–5; task completion.

### T4 — Creator offline (artist/writer/musician)

1. Enable offline mode.
2. Create artifact in Studio workspace.
3. Export (or save local).
4. **Success:** User believes work is safe without Wi-Fi.
5. **Metric:** SUS subset or single ease question.

### T5 — Complexity growth (high school → college)

1. Switch Bicycle → Car → Workshop (guided).
2. Pin vscode (or equivalent).
3. **Success:** User understands they chose more complexity.
4. **Metric:** Preset name recall; preference interview.

### T6 — Research consent (graduate/postdoc)

1. Enter Laboratory preset.
2. Encounter telemetry consent.
3. Export measurement (mock).
4. **Success:** User articulates what data leaves device.
5. **Metric:** Consent comprehension quiz.

---

## 5. Accessibility protocol (P3)

| AT | Platform | Tests |
|----|----------|-------|
| NVDA / JAWS | Windows launcher mock | Home navigation, settings |
| VoiceOver | macOS (if applicable) | Onboarding |
| TalkBack | Android (future handheld) | Touch targets |
| Switch control | Placeholder UI | Document gaps |

Record WCAG 2.2 failures as GitHub issues with `[A11y]` label — not as certification.

---

## 6. Metrics

| Metric | Target (initial hypothesis) | Notes |
|--------|----------------------------|-------|
| Onboarding completion | ≥85% | May revise after P0 |
| Scooter task success (child) | ≥80% with ≤1 caregiver prompt | |
| Guardian trust rating | ≥4/5 on privacy questions | |
| Creator offline confidence | ≥4/5 | |
| Preset comprehension | ≥70% correct metaphor match | scooter/spaceship |
| Critical a11y blockers | 0 P0 before P4 | |

Hypotheses only — not validated claims.

---

## 7. Artifacts to produce

| Artifact | Location |
|----------|----------|
| De-identified session notes | `research/ux/` (create when study runs) |
| Consent forms | External IRB storage |
| Updated claims matrix | CLAIMS_TO_EVIDENCE_USER_EXPERIENCE.md |
| Issue backlog | GitHub `[UX Study]` issues |
| Optional opt-in quotes | README with permission only |

---

## 8. Pre-study engineering prerequisites

Before P1:

- [ ] Launcher mock routes for 12 presets (minimum: Scooter, Car, Studio, Guardian)
- [ ] Onboarding wizard exposed in UI or clickable prototype
- [ ] `tests/test_user_focused_os.py` green in CI
- [ ] `scripts/run_user_focused_os_demo.py` in CI
- [ ] Synthetic demo JSON labeled in participant materials

---

## 9. Ethics and privacy

- No recording of child creative content.
- Aggregate metrics only unless explicit quote consent.
- Guardian must consent for youth sessions.
- Decline telemetry in study devices; use local logs only.

---

## 10. Timeline (proposed)

| Quarter | Activity |
|---------|----------|
| Q3 2026 | P0 heuristic + engineering prerequisites |
| Q4 2026 | P1 moderated usability |
| Q1 2027 | P2 guardian dyads + P3 AT |
| Q2 2027 | P4 field pilot (partner-dependent) |

Dates are planning placeholders, not commitments.

---

## 11. Related documents

- [CLAIMS_TO_EVIDENCE_USER_EXPERIENCE.md](CLAIMS_TO_EVIDENCE_USER_EXPERIENCE.md)
- [USER_FOCUSED_OS_LIMITATIONS.md](USER_FOCUSED_OS_LIMITATIONS.md)
- `docs/EVIDENCE_STANDARD.md`
- `product/CLAIM_BOUNDARY.md`
