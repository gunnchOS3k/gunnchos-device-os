# Independent Golden Acceptance Plan — VP-003 / WP-003

> **VERIFIER OWNED** — independently derived acceptance plan (not an implementer stub).

| Field | Value |
|---|---|
| Owner | Independent verifier (not implementer) |
| Work packet | WP-003 |
| Verification class | V1 |
| Tip under test (claimed) | `6ffab227bfe314903dfd7018e35b6524f2136503` (PR #81 digital remediation re-run; prior: `aa13f2c` / merged #80 `3f230ff`) |
| Accepted main baseline (parent) | Merge base of PR #81 / last accepted `main` at re-run time |
| Derivation sources | MLP, Product Quality Gate, GOLDEN_JOURNEYS.json, Evidence Levels, Depth Ladder, Independent Verification Policy, WP-003 packet, GunnchOS Requirements v0.1, Cycle 1 product promises (Student 14.5, DS-XL, Handheld, Rings, Dock, Ecosystem) |
| Explicitly excluded as design source | Implementer Phase XI/XII journey tests, supporting fixtures/harness runs, scorecard FUNCTIONAL_PASS authored by implementer |
| Digital Cycle 1 target | Evidence **E4**, Depth **D6** where genuinely earned |
| Honesty tokens | `PHYSICAL_PENDING` (E5), `HUMAN_VALIDATION_PENDING` (E6); never promote HUMAN_VALIDATED / PHYSICALLY_VALIDATED |
| Results | `quality/golden_journeys/verifier/RESULTS.md`, `VP-003-RESULT.json`, scorecard `INDEPENDENT_VERIFICATION` fields |

## Independence attestation (pre-execution)

This plan was derived from product contracts and normative outcomes **before** treating implementer-authored journey tests as authoritative. Existing tests may be cited later only as supporting evidence pointers, never as the acceptance design source. Implementer supporting harness PASS is **not** V1 certification.

## Allowed assumptions (Cycle 1 digital)

1. Verification may use digital/simulated device planes that exercise real OS APIs, packages, and cross-app orchestration present on the tip SHA — not scripted narrative stubs alone.
2. “Actual” LMS/browser/email/calendar services may be protocol-compatible fixtures **only if** they exercise the same OS submission/sync/identity surfaces the product claims; pure string mocks without those surfaces do **not** earn D6.
3. Ring input may use accepted digital edge-io packet paths (not physical ring SI) for Cycle 1; physical targeting latency remains PHYSICAL_PENDING.
4. Dock external display/Ethernet/USB power paths that require hardware remain PHYSICAL_PENDING; digital dock session continuity APIs may be assessed for E4/D6 only if a real cross-app session is preserved.
5. Competitor scores are forbidden unless actually measured in this verification. Category strategy labels only.
6. `user_preference` remains `NOT_MEASURED` without humans.

## Disallowed evidence inflation

- Renaming Phase XI/XII or supporting harness PASS as independent E4.
- Claiming D6 for single-module unit tests or schema-only fixtures.
- Claiming E5/E6 or frontier parity.
- Fabricating competitor measurements.
- Accepting silent overwrite, data loss, or revoke gaps as “partially OK” for S0 journeys (GOLDEN-09, GOLDEN-10).

## Product-quality scoring rule

Score dimensions 0–4 per Product Quality Gate from independently observed digital behavior. EVT software bar: **no 0** on Golden Journeys. Visual/interaction scores reflect digital UI surfaces only; preference stays NOT_MEASURED.

---

## GOLDEN-01 — Student assignment → submission → recreation

**MLP anchors:** Student 14.5 (office/browser/LMS, local AI, media/games), Ecosystem continuity.

**Required user/system outcomes**
1. Authenticated student session can open a real assignment (browser/LMS or protocol-compatible service).
2. PDF/reference + office document editable; local gunnchAI help invoked via actual OS AI API (not fake text).
3. Save → upload/submit → **verify receipt** (durable proof of submission).
4. Launch first-party recreation (Anime or Pedestrian/Foot Racing) and save.
5. Return to **intact** document and submission receipt (no corruption, no silent loss).

**Independent failure cases**
- Submit succeeds in UI but no durable receipt.
- Document hash/content changes after recreation interrupt.
- AI help uses cloud-only path when local required, or invents citations.
- Game launch orphans assignment session state.

**Acceptance checks (independent design)**
- A1: End-to-end digital workflow across login → LMS/assignment → doc → AI → submit → receipt → game → return; assert receipt + document integrity markers.
- A2: Negative: kill/suspend mid-recreation; document/receipt still intact.
- A3: AI call routed through OS AI / local gunnchAI surface with observable API boundary.

**Evidence for E4/D6:** Independent execution of cross-app workflow on tip; not unit test alone. Physical LMS campus radio/UI feel = PHYSICAL/HUMAN pending.

---

## GOLDEN-02 — Offline → reconnect

**MLP anchors:** Student 14.5 offline work; Ecosystem sync integrity.

**Required outcomes**
1. Lose network while editing; continue editing offline.
2. Reconnect; conflict-safe sync.
3. **No silent overwrite** of divergent server/local edits.

**Failure cases**
- Offline edit discarded on reconnect.
- Last-write-wins silent overwrite without conflict UX/marker.
- “Synced” flag without content equality proof.

**Acceptance checks**
- B1: Partition network; edit; assert local durable draft.
- B2: Create divergent remote; reconnect; assert conflict detection or merge policy with no silent loss.
- B3: Byte/hash compare of surviving versions vs silent overwrite.

---

## GOLDEN-03 — Creator build/package/install

**MLP anchors:** DS-XL Coder (local build/test/debug/deploy, AI help).

**Required outcomes**
1. Git repo → edit → build → test → debug.
2. gunnchAI code assistance through **real API**.
3. Package → install → run → logs/profile available.

**Failure cases**
- Package produced but not installable/runnable.
- AI assist is stubbed string with no API.
- Tests reported pass without execution.

**Acceptance checks**
- C1: Build+test a sample app from repo tooling on tip.
- C2: Package/install/run and capture logs/profile artifact.
- C3: AI code-assist call hits real OS/API boundary.

---

## GOLDEN-04 — Office dock workflow

**MLP anchors:** Dock; Student 14.5 office/communication.

**Required outcomes**
1. Dock session enables external display/input **or** digital dock plane equivalent with explicit PHYSICAL_PENDING for hardware I/O.
2. Email/calendar + DOCX/XLSX/PPTX/PDF + meeting A/V path + print/export.
3. Undock; **session preserved**.

**Failure cases**
- Undock drops open documents/session.
- Office formats claimed but not openable.
- Print/export is no-op without artifact.

**Acceptance checks**
- D1: Dock → open office set → produce export/print artifact → undock → session continuity assertion.
- D2: Mark hardware display/Ethernet/USB power PHYSICAL_PENDING if not on target SI.

---

## GOLDEN-05 — Handheld play → dock → work → undock

**MLP anchors:** Handheld Hybrid; Dock; Ecosystem.

**Required outcomes**
1. Play first-party game; checkpoint.
2. Dock → desktop/work shell; complete real work task.
3. Undock; **resume accepted game state**.

**Failure cases**
- Checkpoint missing or wrong slot after undock.
- Work task not real (no document/mail/LMS action).
- Mode switch corrupts either side.

**Acceptance checks**
- E1: Game checkpoint digest before dock.
- E2: Docked work task with durable artifact.
- E3: Undock resume digest matches accepted checkpoint.

---

## GOLDEN-06 — DS-XL dual-screen coding

**MLP anchors:** DS-XL Coder.

**Required outcomes**
1. IDE/code on one display plane; terminal/logs/docs/preview on second.
2. AI + build/test/debug usable in that layout.
3. Layout persistence across session restart.

**Failure cases**
- Second plane is cosmetic only (no independent content).
- Layout not restored.
- Build/test not reachable from dual-screen session.

**Acceptance checks**
- F1: Assign distinct workloads to two planes; assert both active.
- F2: Run build/test/debug + AI from layout.
- F3: Restart session; layout restored.
- Hardware dual-panel = PHYSICAL_PENDING if only logical planes digital.

---

## GOLDEN-07 — Ring real input

**MLP anchors:** Rings.

**Required outcomes**
1. Actual edge-io simulated/accepted digital packet path.
2. Type in document; pointer/browser; shortcut; game control.
3. Correct target + confidence; **low-confidence destructive action rejected**.
4. Conventional input fallback works.

**Failure cases**
- Packets accepted without target/confidence gates.
- Destructive action proceeds at low confidence.
- No fallback when ring path unavailable.

**Acceptance checks**
- G1: Inject accepted digital ring packets into doc/browser/game targets.
- G2: Low-confidence destructive attempt → rejected.
- G3: Disable ring path → conventional fallback succeeds.
- Physical ring SI latency/ergonomics = PHYSICAL/HUMAN pending.

---

## GOLDEN-08 — Private local AI tutoring

**MLP anchors:** Student 14.5 local AI; Ecosystem privacy.

**Required outcomes**
1. Authorized assignment/source only.
2. Actual OS AI API + gunnchAI **local** routing.
3. Learning/project memory with citations where needed.
4. Offline success; cloud-denied case still succeeds locally.
5. Privacy isolation (no unauthorized exfil / cross-user leak).

**Failure cases**
- Cloud path used when denied/offline required.
- Memory leaks across identities.
- Uncited factual tutoring presented as sourced.

**Acceptance checks**
- H1: Local route with network denied → tutoring succeeds.
- H2: Unauthorized source rejected.
- H3: Cross-identity memory isolation probe.
- H4: Citation/source binding where claim requires it.

---

## GOLDEN-09 — Failed update rollback (S0)

**MLP anchors:** Student 14.5 safe update/recovery; security V1.

**Required outcomes**
1. Actual A/B or equivalent image mechanism.
2. Bad update → health failure → **rollback**.
3. **User data intact** (zero loss).

**Failure cases**
- Rollback reported without slot switch.
- User data mutated/lost across rollback.
- Health gate bypassed.

**Acceptance checks**
- I1: Install bad image to inactive slot; boot/health fail; rollback to prior.
- I2: User data hash pre/post identical for protected paths.
- I3: S0: any data loss or failed rollback = FAIL (blocking).

---

## GOLDEN-10 — Lost-device revoke (S0)

**MLP anchors:** Ecosystem identity/trust; security V1.

**Required outcomes**
1. Trusted-device identity established.
2. Revoke session/device.
3. Continuity access **denied** afterward.
4. Private files/memory unavailable to revoked identity.
5. Local recovery path for legitimate owner exists and is distinct from revoked path.

**Failure cases**
- Revoked token still opens continuity/private memory.
- No recovery path (bricks owner) **or** recovery path usable by revoked identity.
- Revoke is UI-only without enforcement.

**Acceptance checks**
- J1: Establish trusted device; access private continuity.
- J2: Revoke; assert denial on continuity + private files/memory.
- J3: Owner local recovery succeeds without re-enabling revoked identity.
- J4: S0: any post-revoke private access = FAIL (blocking).

---

## Evidence & depth adjudication rules

| Claim | Requires |
|---|---|
| E4 | This independent plan + independent execution results against tip SHA + defects filed on failure |
| D6 | Real cross-app user workflow observed end-to-end (multiple apps/services), not single module |
| E3/D5 or below | May be recorded honestly when only integrated automation or single-app depth is earned |
| PHYSICAL_PENDING | Hardware dock/display/radio/ring SI not exercised |
| HUMAN_VALIDATION_PENDING | No human preference/usability study |

## Environment record (filled at execution)

- Verifier identity: independent VP-003 verifier agent (re-run after digital remediation)
- Date: 2026-08-10
- Repo path / worktree: `/tmp/gunnchos-device-os-vp003-verify` (PR #81 tip)
- Tip SHA: confirm via `git rev-parse HEAD` at execution (`6ffab227…` claimed)
- Method: contract-derived checks; probe OS APIs/runtimes/packages; optional supporting harness only as secondary citation; implementer `digital_paths` helpers treated as tip surfaces under test, not as V1 certification

## Exit criteria for VP-003 digital

1. This plan committed on PR branch.
2. Per-journey RESULTS + scorecard INDEPENDENT_VERIFICATION updated honestly (PASS/FAIL/PARTIAL).
3. COMPETITOR_READINESS_GAP_MATRIX reviewed; reject fabricated scores.
4. S0/S1 failures filed as blocking defects.
5. Distinguish gates:
   - **DIGITAL_INDEPENDENT_V1 PASS** when digital-core journeys (G01/G02/G03/G05/G09/G10) independently PASS at earned E4/D6 (G09 may remain digital A/B D5) and G04/G06/G07/G08 are PASS or honesty PARTIAL with explicit PHYSICAL_PENDING (E5) / HUMAN_VALIDATION_PENDING (E6).
   - **Full physical/human V1 PASS** only if all 10 journeys independently PASS without PARTIAL caps; otherwise FAIL with defect list while DIGITAL_INDEPENDENT_V1 may still PASS.
