# MLV / WAIKE / 7GC AI-RAN convergence

Additive gunnchOS continuity on top of PR #165. This branch does not replace WAIKE, 3k MLV, field-kit, the digital twin, SpectrumX, or Edge-IO.

## Systems of record

| System | Authority |
|---|---|
| WAIKE | learning system of record |
| 3k MLV | Home / Campus / Gallery + Network Twin UX |
| field-kit | AI-RAN contract, evidence, actuation-policy authority |
| 7GC Digital Twin | network / scenario twin transformation |
| SpectrumX | planning / AI-RAN policy engine |
| Edge-IO | measurement / evidence source |
| gunnchOS | shell, registry, intents, lifecycle, return continuity |

gunnchOS does not duplicate course data, gradebooks, twin solvers, RIC adapters, or measurement pipelines.

## Foundation preserved

PR #165 remains the MLV registration, private-default artifact schema, share-token redaction, and journey-preset policy PR.

This child adds versioned `v2` product intents for the current graph:

```text
gunnchos://mlv/home
gunnchos://mlv/campus
gunnchos://mlv/campus/<campus_id>
gunnchos://mlv/campus/network-twin
gunnchos://mlv/campus/network-twin/<campus_id>
gunnchos://mlv/campus/network-twin/<campus_id>/run/<run_id>
gunnchos://mlv/campus/network-twin/<campus_id>/shadow/<run_id>
gunnchos://mlv/gallery
```

Canonical campus IDs: `gary`, `ghana`, `guyana`, `geelong`, `germany`, `gaza`, `graham_land`. `graham-land` is accepted as an alias.

MLV stays **one app**. Campuses, WAIKE-inside-MLV, and Network Twin are semantic subroutes, not seven extra registry apps. WAIKE remains its own learning application.

## Learner journey

```text
gunnchOS → MLV → Campus → WAIKE Academic Center
→ GET /api/v1/mlv/consumer-summary
→ Continue Learning / Due Soon / Courses
→ waike:// deep link → WAIKE
→ return to the same MLV campus
```

Pinned WAIKE contract: PR #25 `f0176c2c45c1c366ad22f46407e6c55c3c5f3e8e`.

Readiness truth stays 18 imported / 16 READY / 2 PARTIAL (`DIGITAL_CONFIDENCE`, `IT_SUPPORT_HARDWARE`). Do not upgrade to 18 READY.

If WAIKE is unavailable, gunnchOS returns a labeled `OFFLINE DEMO` campus surface. It does not fabricate live connectivity or a shadow LMS.

## Network Twin journey

```text
gunnchOS → MLV → Campus → one of 7 twins
→ Network Twin Lab → digital proposal
→ synthetic/backend optimization → Pareto
→ DIGITAL SHADOW recommendation → return to campus
```

Allowed modes: `SIMULATION ONLY`, `READ ONLY`, `RECOMMENDATION ONLY`, `SHADOW`.

Disabled: `AUTHORIZED TESTBED`, `PRODUCTION`. `REAL_ACTUATION_ENABLED=false`.

gunnchOS does not hold E2, radio, SpectrumX, or Edge-IO secrets. Backend provenance is version-pinned only.

## Privacy and truth

- Home stays private. Gallery stays public-only. Share tokens are never echoed.
- Learner grades / assignments / mastery / identity history must not join signal telemetry / movement / RAN optimization.
- Gaza routes stay on abstract zones. Precise location and public-vulnerability routes are rejected.
- Graham Land is remote-first / simulation / partner-reference. No fake WAIKE station and no ownership implication.

## Artifacts

- `shared_contracts/mlv_continuity_intent.v2.schema.json`
- `shared_contracts/WAIKE_MLV_EDUCATION_CONTRACT.v1.json`
- `artifacts/integration/MLV_WAIKE_7GC_AIRAN_JOURNEY_MATRIX.json`
- `artifacts/integration/MLV_WAIKE_7GC_AIRAN_CONVERGENCE_GATES.json`

Human, Pixel, hosted, physical, and merge gates remain false until separately proven.
