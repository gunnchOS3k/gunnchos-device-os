# Independent Golden Acceptance Plan — VERIFIER OWNED

> **Implementer stub only (WP-003).**  
> The independent verifier writes the real plan **before** inspecting prior Phase XI/XII journey tests.  
> Do not treat supporting harness results as the independent test design source.

## Status

- Owner: **independent verifier** (not implementer)
- Work packet: WP-003
- Linked scorecards: `quality/golden_journeys/scorecards/GOLDEN-*.scorecard.json`
- Linked fixtures: `quality/golden_journeys/fixtures/GOLDEN-*.fixture.json`
- Results location (verifier fills): `quality/golden_journeys/verifier/INDEPENDENT_GOLDEN_ACCEPTANCE_RESULTS.md`

## Instructions for verifier

1. Draft acceptance cases for GOLDEN-01..10 from the product outcomes in WP-003 / `GOLDEN_JOURNEYS.json`.
2. Only afterward consult supporting Phase XI IDs as optional evidence pointers.
3. Record PASS/FAIL per journey into scorecards’ `INDEPENDENT_VERIFICATION` fields.
4. Target digital Cycle 1: evidence **E4**, depth **D6**. Keep `PHYSICAL_PENDING` and `HUMAN_VALIDATION_PENDING`.
5. Do not set frontier parity tokens true. Do not promote HUMAN_VALIDATED or PHYSICALLY_VALIDATED.

## Plan content (verifier replaces this section)

_TODO — verifier writes:_

- Allowed assumptions
- Required user/system outcomes per GOLDEN-01..10
- Independently derived failure cases
- Acceptance test design
- Evidence required
- Environment / identity / date

## Implementer non-claims

- `INDEPENDENT_VERIFICATION.status` remains `PENDING` until verifier executes.
- Supporting subset runs under `artifacts/golden_journeys/` are **not** independent verification.
