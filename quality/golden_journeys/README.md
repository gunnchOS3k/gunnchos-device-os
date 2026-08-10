# Golden Journeys (WP-003) — Implementer Infrastructure

Infrastructure for **true independent verification** of GOLDEN-01..10.

This tree is owned by the **implementer** for hooks, schemas, fixtures, and supporting regression.  
The **independent verifier** owns `verifier/INDEPENDENT_GOLDEN_ACCEPTANCE_PLAN.md` and results.

## Distinctions (do not collapse)

| Field | Meaning |
|---|---|
| `FUNCTIONAL_PASS` | Supporting digital checks (may use Phase XI as regression only) |
| `PRODUCT_QUALITY_SCORE` | 0–4 dimensions; `user_preference` stays `NOT_MEASURED` without humans |
| `INDEPENDENT_VERIFICATION` | Verifier-only E4/D6 acceptance |
| `PHYSICAL_PENDING` | Always pending until E5 |
| `HUMAN_VALIDATION_PENDING` | Always pending until E6 |

## Layout

- `GOLDEN_JOURNEYS.json` — catalog
- `PATH_TO_JOURNEY_MAP.json` — major-PR path → subset map
- `schemas/quality_scorecard.schema.json` — scorecard schema
- `scorecards/GOLDEN-*.scorecard.json` — per-journey scorecards
- `fixtures/GOLDEN-*.fixture.json` — verifier support fixtures
- `COMPETITOR_READINESS_GAP_MATRIX.json` — readiness gaps (no fabricated competitor scores)
- `verifier/` — independent plan/results stubs (verifier-owned content)
- `runs/` — supporting harness outputs (not independent)

## Commands

```bash
# Validate scorecard/fixture/matrix structure
PYTHONPATH=.:src python3 scripts/validate_golden_journey_scorecards.py

# Select + run supporting subset for changed paths
PYTHONPATH=.:src python3 scripts/run_golden_journey_subset.py --path gunnchos_device_os/dock_manager.py

# All ten supporting journeys (still not independent verification)
PYTHONPATH=.:src python3 scripts/run_golden_journey_subset.py --all

# Merge recommendation (S0/S1 supporting failures block; auto-merge always off)
PYTHONPATH=.:src python3 scripts/recommend_merge_golden.py --all
```

## Doctrine

- Do not rename Phase XI/XII tests as independent.
- Do not set frontier parity tokens true.
- Do not claim HUMAN_VALIDATED or PHYSICALLY_VALIDATED.
- Draft PRs only; never auto-merge.
