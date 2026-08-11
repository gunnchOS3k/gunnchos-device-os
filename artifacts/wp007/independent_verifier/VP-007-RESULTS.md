# VP-007R Independent Verifier Results (Cycle 2)

**overall_result: PASS**  
**INTERNAL_RED_TEAM_READY: true** (`independent_verified=true`)  
**Accepted main:** `3908de7c35882b500368475ce13d2243435f6443`  
**Remediation tip:** `7e5ab2f290704ea3fde3b05a23cc171bc901fefb` (#94 MERGED)  
**Executed:** 2026-08-10T22:27:47Z

## Independence

Attack plan refreshed from VP-007/WP-007R, trust boundaries, Golden Journeys, and accepted architecture **before** treating implementer `*_PREPARED` as PASS.

- Plan: `artifacts/wp007/independent_verifier/INDEPENDENT_ATTACK_PLAN.md`
- Runner: `artifacts/wp007/independent_verifier/run_independent_attacks.py`
- Results: `artifacts/wp007/independent_verifier/INDEPENDENT_ATTACK_RESULTS.json` — **35/35 PASS, S0=0, S1=0**

## Defect / residual closures

| ID | Independent status |
| --- | --- |
| WP007-IV-DEF-001 (lab CI) | CLOSED (reconfirmed) |
| WP007-IV-RES-001 updater crypto | **CLOSED_DIGITAL** (Ed25519; force cannot set verified=True; PRODUCTION EXTERNAL_PENDING) |
| WP007-IV-RES-002 hostile network digital | **HOSTILE_NETWORK_DIGITAL=E4_PASS** (RF E5/E8 EXTERNAL_PENDING) |
| WP007-IV-RES-003 local save integrity | **LOCAL_SAVE_INTEGRITY_DIGITAL=E4_PASS** (AUTHORITATIVE_MULTIPLAYER EXTERNAL_PENDING) |

## Device Lab containment

| Probe | Result |
| --- | --- |
| Unapproved path | DENIED (IV-LAB-001) |
| Unregistered temp | DENIED (IV-LAB-002) |
| Host `/etc` register | DENIED (IV-LAB-003) |
| Registered controlled root | ALLOWED; escape still denied (IV-LAB-004) |
| Default instances root | ALLOWED (IV-LAB-005) |

## Supporting evidence

- Implementer harness (comparison only): 15/15, S0=0, S1=0
- `pytest` wp007 + device_lab containment/foundation: PASS
- Golden Journeys merge gate: `supporting_run_ok=true`, blockers=[]
- CI on #94 / accepted main: GREEN (test, gate1, digital-red-team, GJ, security jobs)
- `WP007_CANONICAL_EVIDENCE_CONTRADICTIONS=0`
- FAIL history preserved: `artifacts/wp007/history/VP-007-RESULT.initial-fail.0e46609b3d86241f2c282e7a1f3752d16d2bba67.json`

## Claim boundary

INTERNAL_RED_TEAM_READY at E4 digital only. **Not** production_ready. EXTERNAL pentest, RF field, production trust root, and authoritative multiplayer remain EXTERNAL_PENDING.

## Edmund

- #94 already MERGED — remediation accepted
- This verifier PR: **keep DRAFT**, evidence-only, do not merge as readiness theater
- Field-kit Cycle 2 correction **may proceed** to align aggregate readiness with this Independent PASS
