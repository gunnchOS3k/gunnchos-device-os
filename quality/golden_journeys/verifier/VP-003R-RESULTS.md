# VP-003R Independent Results

Tip: `a65ff495bf9855a4f8df88beae2a8c5241ccd8af` (PR #84 DRAFT)  
Baseline main: `44294d6485d8d82fe69191c6e585f13ab7c63f63`  
Plan: `quality/golden_journeys/verifier/INDEPENDENT_WP003R_ACCEPTANCE_PLAN.md`  
Executed: 2026-08-10T18:24:17Z

## Lab foundation
**PASS** (ADR-010, profiles, `gunnchctl`, fidelity honesty FAIL conditions, VF4/5/6 PHYSICAL_PENDING, SILICON_EXACT=false, manifests, local UI).

## Per-journey Independent

| Journey | IV | E | D | Notes |
|---|---|---|---|---|
| G01 | PASS | E4 | D6 | Regression |
| G02 | PASS | E4 | D6 | Regression |
| G03 | PASS | E4 | D6 | Regression |
| G04 | PASS | E4 | D6 | Lab dock lifecycle; PHYSICAL_DOCK PENDING |
| G05 | PASS | E4 | D6 | Regression |
| G06 | PARTIAL | E4 | D5 | Dual outputs OK; GJ-DEFECT-006 |
| G07 | FAIL | E3 | D5 | GJ-DEFECT-007 |
| G08 | PASS | E4 | D6 | Real llama on tip; HUMAN/HW PENDING |
| G09 | PASS | E4 | D5 | Regression |
| G10 | PASS | E4 | D6 | Regression |

## Overall
**FAIL** — WP-003R digital depth not closed (G06/G07).

## Edmund merge #84?
**No** — keep DRAFT. CI green ≠ Independent closure.
