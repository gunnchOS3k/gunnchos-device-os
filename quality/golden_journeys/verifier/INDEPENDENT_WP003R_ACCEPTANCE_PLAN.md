# Independent WP-003R Acceptance Plan — VP-003R / Device Lab

> **VERIFIER OWNED** — independently derived **before** treating WP-003R remediation tests, Lab scenario helpers, or implementer `ok=true` as authoritative.

| Field | Value |
|---|---|
| Owner | Independent verifier (not implementer) |
| Work packet | WP-003R (Cycle 1 residual; not Cycle 2; not WP-005+) |
| Verification packet | VP-003R |
| Tip under test (claimed) | `a65ff495bf9855a4f8df88beae2a8c5241ccd8af` (device-os DRAFT PR #84) |
| Accepted main baseline | `44294d6485d8d82fe69191c6e585f13ab7c63f63` (post-#83; verify against PR base) |
| Companion ACTIVE_WIP | field-kit DRAFT PR #60 |
| Derivation sources | MLP (`MINIMUM_LOVABLE_PRODUCT.md`); Product Quality Gate; GOLDEN_JOURNEYS.json; Evidence Levels; Depth Ladder; WP-003R master packet; gunnchDevice Lab Foundation v0.1 requirements; VP-003R verifier addendum; product charter / operating-model dock/DS-XL/Ring/AI promises |
| Explicitly excluded as design source | Implementer `tests/device_lab/*`, Lab scenario self-PASS, `gunnchctl test` exit alone, scorecard FUNCTIONAL_PASS authored by implementer, prior PARTIAL D5 closure claims |
| Digital target | Evidence **E4**, Depth **D6** where digitally achievable via Device Lab VF1/VF2 |
| Honesty | VF4/VF5/VF6 = PHYSICAL_PENDING; HUMAN tutoring quality = PENDING; no frontier parity; `SILICON_EXACT_EMULATION=false` unless truly supported |
| Results | `VP-003R-RESULT.json`; updated scorecard `INDEPENDENT_VERIFICATION`; this plan |

## Independence attestation (pre-execution)

This plan was written from product/Lab contracts **before** reading remediation tests as acceptance design. Existing Lab scenarios may be used later only as **supporting evidence** after independent probes of runtime state (outputs, input chain, model/runtime, manifests, fidelity panel). Implementer harness PASS is not V1 Independent PASS.

## Governing ladders

- **E4**: Independent digital verification of real integrated behavior (not unit/schema alone).
- **D6**: Cross-app real user workflow through the product stack.
- **E5**: Target-hardware validation (physical dock SI, panels, ring pose, HW AI perf) — PENDING for WP-003R.
- **E6**: Human/user validation (tutoring quality, preference) — PENDING.

## Device Lab foundation acceptance (LAB)

### L-ADR
ADR-010 exists and records Class D approval, fidelity boundaries, hybrid virtualization honesty, and non-claims (not E5/E6, not silicon-exact, not EVT-calibrated).

### L-PROFILE
Versioned device profile schema exists with LAB-004 minimum fields. Catalog includes `student_14_5`, `dsxl_coder`, `handheld_hybrid`, `handheld_docked`, `edge_io_rings`, `full_ecosystem`. Profiles must not invent frozen hardware; unknown props = `TARGET_TBD`. Deep execution maps: G04→handheld_docked, G06→dsxl_coder, G07→edge_io_rings+target, G08→student_14_5 (+ local AI).

### L-CLI
Public CLI invocable for automation (names may follow repo convention):
`gunnchctl test GOLDEN-04|06|07|08` (and devices/start/stop/scenario/status/evidence as Foundation allows).
CLI PASS alone is **insufficient**.

### L-FIDELITY
Every run exposes machine-readable fidelity classification. WP-003R digital targets:
- VF1 SOFTWARE VIRTUAL DEVICE = REQUIRED
- VF2 PERIPHERAL BEHAVIOR = REQUIRED for G04/G06/G07
- VF3 MODELED PERFORMANCE = foundation/schema only; never labeled physical
- VF4/VF5/VF6 = PHYSICAL_PENDING

**Independent FAIL if any of:**
1. Modeled performance / RF / battery / thermal labeled as physical or measured.
2. DS-XL profile claims two displays while compositor/session exposes one output (G06 D6 FAIL).
3. Stub Dock boolean/`{docked:true}` stands in for VF2 dock peripheral lifecycle.
4. Direct file write claims Ring real-input D6 (bypasses input stack).
5. Deterministic/templated tutor (`micro-deterministic-v1` or equivalent) claimed as primary real-model D6.
6. Calibration / PHYSICAL_CORRELATION claimed without EVT evidence.
7. Screenshot/mock UI stands in for real virtual gunnchOS session without honesty marking.
8. Profile declares hardware unsupported by accepted requirements.
9. Run manifests omit accepted SHAs / image or runtime hashes / fidelity / limitations.
10. `SILICON_EXACT_EMULATION=true` without true SoC replica support.

### L-MANIFEST
Each Lab run emits reproducible manifest: run_id, timestamp, host, hypervisor/backend, profile+version, accepted SHAs, OS/runtime identity, scenario, apps, virtual devices, fidelity levels, measurement types, artifacts/checksums, PASS/FAIL, limitations.

### L-UI
Local 127.0.0.1 developer UI with device selection, dock/network/storage/ring controls, fidelity panel, evidence — required for Foundation v0.1; hosted Lab is LAB-FUTURE (must not expand scope).

### L-BACKEND
Honest hybrid allowed: real gunnchOS APIs/services/compositor paths with `BEHAVIORAL_DEVICE_PROFILE=true` and `SILICON_EXACT_EMULATION=false` when full QEMU guest is impractical in CI. Prefer real OS surfaces over Python imitation of the product.

---

## GOLDEN-04 — Office dock (LAB-SCENARIO-OFFICE-DOCK)

**MLP:** Dock (power, displays, Ethernet, USB, audio; clean mobile↔workstation transitions); Student/Handheld office/communication.

**Required digital D6 outcomes**
1. Profile `handheld_docked` (or accepted dockable compute) via Lab scenario `LAB-SCENARIO-OFFICE-DOCK`.
2. Undocked → attach virtual dock → **actual** virtual capabilities appear: external display, Ethernet route, dock audio route, input/desktop profile, print/export path, charging/power metadata as applicable.
3. Cross-app office work: docs (format audit), email/calendar, meeting A/V path, print/export.
4. Detach dock → virtual dock devices disappear; files/session/window state preserved.
5. Format audit honest for DOCX/XLSX/PPTX/ODT/ODS/ODP/PDF/CSV/Markdown — unsupported formats explicit, not buried under PASS.

**Independent FAIL**
- Primary proof is `{docked:true}` / stub state without lifecycle capability add/remove.
- Format `ok=false` hidden under overall PASS.
- Claims physical dock SI / E5.

**Target if earned:** FUNCTIONAL PASS; E4; D6; Independent PASS; `PHYSICAL_DOCK_VALIDATION=PENDING`; HUMAN PENDING.

---

## GOLDEN-06 — DS-XL dual-screen (LAB-SCENARIO-DSXL-DUALSCREEN)

**MLP:** DS-XL Coder — real local build/test/debug/deploy with **two useful screens**, AI help.

**Required digital D6 outcomes**
1. Profile `dsxl_coder`; scenario `LAB-SCENARIO-DSXL-DUALSCREEN`.
2. **Two real compositor/session outputs** (DISPLAY-A primary, DISPLAY-B secondary) — not a logical label alone.
3. Real apps on correct outputs (IDE/editor primary; terminal/docs/logs/tests secondary).
4. Focus/input moves correctly; build/test/debug executes; AI help via OS AI API.
5. Layout persists/reloads; secondary disconnect degrades safely; reconnect restores layout.
6. No `unknown transition` accepted as success.

**Independent FAIL**
- One compositor output while claiming two-display D6.
- Unknown transition treated as success.
- Physical panel/hinge/touch claimed.

**Target if earned:** E4/D6 Independent PASS; physical panels E5 PENDING.

---

## GOLDEN-07 — Ring real input (LAB-SCENARIO-RING-REAL-INPUT)

**MLP:** Rings — reliable system input with targeting/confidence; typing/pointer/shortcuts/gaming; conventional fallback.

**Required digital D6 chain**
```
edge-io firmware/sensor simulator → authenticated Ring packet → gunnchOS Ring service
→ SpatialInputService → target/confidence → input router / virtual HID / Wayland injection
→ focused application state change
```
Exercise document, browser GUI, and one first-party game with **observable app/game state** change through the stack. Safety: low-confidence destructive reject; wrong-target reject; explicit target feedback; Ring unavailable → conventional fallback.

**Independent FAIL**
- Direct file write / adapter map as primary D6 proof.
- Bypass of Ring/input stack.
- Physical pose/latency/drift claimed.

**Target if earned:** E4/D6 Independent PASS; physical pose E5/E6 PENDING.

---

## GOLDEN-08 — Private local AI tutoring (LAB-SCENARIO-LOCAL-AI-TUTOR)

**MLP:** Student local AI; authorized tutoring with sources/privacy/fallback.

**Required digital D6 outcomes**
1. Scenario offline or cloud-denied.
2. **Primary** path uses real accepted local inference runtime/model (llama.cpp or accepted equivalent) — **not** `micro-deterministic-v1` as primary tutoring proof.
3. Record model ID/hash/license, runtime, router decision, RAG/memory sources, citations, host latency/RAM as **reference only**.
4. Workflow: WAIKE/student surface → authorized sources → OS AI API → router → real local model → cited response → memory update → continue assignment.
5. Negatives: offline; cloud denied; user/project isolation; memory disable/delete; citation supports response; unauthorized source excluded.

**Independent FAIL**
- Deterministic/templated stub as primary D6 claim.
- Host latency labeled target-hardware performance.
- Human tutoring quality claimed without E6.

**Target if earned:** E4/D6 Independent PASS; `HUMAN_TUTOR_QUALITY=PENDING`; `TARGET_HARDWARE_AI_PERFORMANCE=PENDING`.

---

## Regression (must not regress)

Independently re-probe (or re-run prior V1 surfaces on tip):

| Journey | Required digital floor |
|---|---|
| G01 | Independent PASS D6 |
| G02 | Independent PASS D6 |
| G03 | Independent PASS D6 |
| G05 | Independent PASS D6 |
| G09 | Independent PASS (S0) |
| G10 | Independent PASS D6 |

Regression FAIL if tip breaks prior digital proof surfaces.

---

## Product quality floor (G04/G06/G07/G08)

Per Product Quality Gate 0–4: no digitally observed **0**; no silent digitally-fixable **1** without filed `GJ-DEFECT-###`. Do not fabricate `user_preference` (remains `NOT_MEASURED`).

## Competitor matrix

Update review ACCEPT/FAIL without fabricating scores. Strategy labels only unless measured. Record new E/D and remaining E5/E6/E7 gaps.

## Desired digital table (earn only if genuine)

```
G01–G10 Independent PASS at D6 where digitally achievable;
else PARTIAL with precise physical/human reason.
```

## Defect policy

Open `GJ-DEFECT-###`. S0/S1 blocks closure. Digital S2 inside these journeys should be fixed or filed — do not relabel digital S2 as physical without explaining why a digital Lab reference cannot exercise it.

## Explicit non-claims for this packet

- Not EVT physical twin calibration (VF4+)
- Not frontier OS parity
- Not silicon-exact SoC emulation
- Not human tutoring quality
- Not LAB-FUTURE-001..009 execution

## Execution order for this verifier

1. Freeze this plan (done).
2. Independently inspect Lab foundation + fidelity honesty (including FAIL conditions).
3. Independently probe G04/G06/G07/G08 runtime evidence beneath `gunnchctl` (do not trust CLI alone).
4. Regression G01/G02/G03/G05/G09/G10.
5. Competitor matrix honesty review.
6. Emit `VP-003R-RESULT.json` + update scorecard `INDEPENDENT_VERIFICATION`.
