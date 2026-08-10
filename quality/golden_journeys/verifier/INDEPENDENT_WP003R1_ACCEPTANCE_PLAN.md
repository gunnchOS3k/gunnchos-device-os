# Independent WP-003R.1 Acceptance Plan — VP-003R.1 / G04 privileged integrity

> **VERIFIER OWNED** — derived **before** treating implementer remediation tests, privileged CI job self-PASS text, or `ok=true` as Independent PASS.
> Written 2026-08-10T20:22:00Z against tip under test (claimed `645d31a`; verify ⊆ accepted main after #88).

| Field | Value |
|---|---|
| Owner | Independent verifier (not implementer) |
| Work packet | WP-003R.1 (Cycle 1 integrity closure; not Cycle 2; not WP-005+) |
| Verification packet | VP-003R.1 |
| Tip under test (claimed) | `645d31a6b795b461afb1c66982b1402ffa373237` (#88 head) |
| Accepted main at verify | `801b332ba2025b5ddfd8f85cebbafa2c2c368e02` (Merge #88; contains tip) |
| Prior product baseline | #85 `67e10ea` / `0449cbb`; #87 `b82504d` (G04 privileged job broken) |
| Derivation sources | ACTIVE_WIP WP-003R.1 scope A/B/C; DEFECT_BACKLOG GJ-DEFECT-005 honest_cap; Lab VF2 fidelity rules; EVIDENCE_LEVELS E4; DEPTH_LADDER D6; prior VP-003R plan (G04 dock lifecycle) |
| Explicitly excluded as design source | Implementer `proposed_independent_status`; implementer print(`…PASS…`); harness `ok=true` alone |
| Honesty | VF4/5/6 PHYSICAL_PENDING; no frontier parity; `SILICON_EXACT_EMULATION=false` |

## Independence attestation (pre-execution)

This plan states G04 E4 reference requirements from WP-003R.1 / Lab honesty caps **before** treating privileged CI remediation assertions as authoritative. CI job success is later used only as **supporting machine evidence** that those independently required asserts executed green. Logical FALLBACK_ONLY is never E4 G04 reference proof.

## A — CI integrity (Independent FAIL if any required red)

Required GREEN on verifier tip SHA:

1. Scorecard schema + fixtures
2. test
3. Gate1 (`gate1`)
4. Golden Journeys — Supporting subset + S0/S1 merge gate
5. Golden Journeys — **G04 privileged netns + virtual audio (E4 reference)** if present

No waiver of red required jobs.

## B — GJ-DEFECT-005 / G04 E4 reference (Independent derivation)

### B1. What earns E4 G04 net+audio reference

All of the following are **required** for Independent E4 reference proof of GJ-DEFECT-005 closure:

1. **Virtual Ethernet lifecycle (real):** create netns + veth pair; iface visible in ns; **actual packet transfer** host↔ns (UDP payload match and/or ICMP); detach with cleanup verified (iface/ns gone).
2. **Virtual audio route lifecycle (real):** create PipeWire/Pulse null-sink **or** ALSA snd-aloop equivalent; sink/device appears; stream/probe exercises the route; detach removes/disappears the virtual route.
3. Combined office-dock / Lab path reports `network_backend.e4_reference_proof=true` **and** `audio_backend.e4_reference_proof=true`.
4. `VF2_REQUIRED_GOLDEN_BACKENDS=PASS` only when (3) holds.
5. Honesty retained: `VF2_UNPRIVILEGED_FALLBACK=AVAILABLE`; `VF3=MODELED_ONLY`; `VF4/VF5/VF6=PHYSICAL_PENDING`; `SILICON_EXACT_EMULATION=false`.

### B2. What must NOT count as E4 G04 reference

- Logical / in-memory net attach (`FALLBACK_ONLY`, `NOT_E4_REFERENCE_PROOF`, `packet_transfer.method=logical_in_memory`)
- Logical / in-memory audio route without real sink/loopback lifecycle
- Unprivileged smoke that only proves fallback availability
- Implementer narrative “remediated” without privileged path evidence

### B3. Closure rule

- `CLOSED_INDEPENDENT_PASS` **only if** Independent confirms B1 on tip (code + privileged CI machine evidence + local fallback honesty) **and** B2 holds.
- Else keep `OPEN` with reason.

## C — Competitor matrix

Independent FAIL if:

- `COMPETITOR_MATRIX_CONTRADICTIONS != 0` via `validate_competitor_matrix_consistency` / scorecard validator
- Narrative D6 PASS vs structured depth ≠ D6 (non-pending language)
- `competitor_score` non-null without real benchmarks
- `independent_verification=PASS` without `evidence_refs`
- Bulk-promoted capabilities inconsistently (IV=PASS without E4+D6)

## Journeys (Independent expectations)

| Journey | Expectation |
|---|---|
| G04 | E4/D6 PASS with **real** privileged net+audio backends for GJ-DEFECT-005; PHYSICAL_DOCK still PENDING |
| G06/G07/G08 | E4/D6 PASS retained (no regression vs VP-003R) |
| G01/G02/G03/G05/G10 | no regression |
| G09 | E4/D5 accepted |

## Deliverables

- `VP-003R.1-RESULT.json` (this packet)
- This plan
- Defect backlog / matrix / G04 scorecard updates **only** if Independent results change and validators remain green
- Push onto #88 **or** (if #88 merged/non-draft) **new DRAFT** verifier-artifacts PR only; never merge; auto-merge off
