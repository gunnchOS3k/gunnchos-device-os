# VP-003R Independent Results (re-run post #85)

Tip under test: `67e10ea1d329703d4764fb3799c5244e9781cd97` (contained in accepted main)  
Accepted main: `0449cbb64da416c3b702dcd880d76946e96eb16e` (Merge #85)  
Prior FAIL tip: `a65ff495…` (PR #84 era)  
Plan: `quality/golden_journeys/verifier/INDEPENDENT_WP003R_ACCEPTANCE_PLAN.md`  
Executed: 2026-08-10T18:56:02Z

## Lab foundation
**PASS** (ADR-010, profiles, `gunnchctl`, 127.0.0.1 UI, fidelity honesty FAIL conditions, VF4/5/6 PHYSICAL_PENDING, SILICON_EXACT=false, manifests).

## Per-journey Independent

| Journey | IV | E | D | Notes |
|---|---|---|---|---|
| G01 | PASS | E4 | D6 | Regression |
| G02 | PASS | E4 | D6 | Regression |
| G03 | PASS | E4 | D6 | Regression |
| G04 | PASS | E4 | D6 | Lab dock lifecycle; PHYSICAL_DOCK PENDING |
| G05 | PASS | E4 | D6 | Regression |
| G06 | PASS | E4 | D6 | Dual outputs + real windows + executed toolchain; panels PENDING |
| G07 | PASS | E4 | D6 | Stack mutations doc/browser/game; ring SI PENDING |
| G08 | PASS | E4 | D6 | Real llama primary; fail-closed micro; HUMAN/HW PENDING |
| G09 | PASS | E4 | D5 | Regression |
| G10 | PASS | E4 | D6 | Regression |

## Overall
**PASS** — WP-003R digital Independent residuals (G06/G07/G08 D6) closed on accepted-main tip content.

Artifact DRAFT PR: https://github.com/gunnchOS3k/gunnchos-device-os/pull/86

## Edmund / next
- Keep this verifier-artifact PR **DRAFT** (auto-merge off).
- Accepted-main **product** reproof is **not** next — tip already on `origin/main`.
- After Edmund review: optionally merge artifact DRAFT only; physical/human remain PENDING; do not auto-start WP-005+.
