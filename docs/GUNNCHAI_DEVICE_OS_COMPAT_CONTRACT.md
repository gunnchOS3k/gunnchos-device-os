# gunnchAI3k ↔ device-os compatibility contract

**Evidence class:** ACCEPTED_MAIN (not PREVIEW)  
**Pairing:** device-os `d5c2d17` (#121) × gunnchAI `d357846` (#43)

## Purpose

Device OS integrates tutoring via `gunnchai_integration` and first-party
`run_gunnchai_tutor`. gunnchAI3k owns model routing, memory, and Stage 2
capability HTTP. This contract pins the accepted-main SHA pairing and documents
what device-os may assume — without hidden cross-repo coupling.

## Pin file

`cross_repo_gunnchai_bridge/GUNNCHAI_COMPAT_CONTRACT.json`

Refresh only when Edmund merges a new accepted-main pairing. Do not ingest
unmerged gunnchAI branches as accepted-main.

## API surface (device-os callers)

| Layer | Owner | Entry |
| --- | --- | --- |
| OS safety gates + local template | device-os | `gunnchai_integration` |
| First-party SDK tutor | device-os | `first_party_apps.gunnchai_tutor` |
| Stage 2 capability HTTP | gunnchAI3k | `GET /health`, `GET /v1/capabilities`, `POST /v1/capability/*` |
| Cross-product smoke | device-os | `phase_xiv.callers.CrossProductCallers` |

Authoritative Stage 2 note: gunnchAI3k `artifacts/stage2/OS_CALLER_CONTRACT.md` at
pinned SHA.

## Honesty tokens device-os may assume (#43)

| Token | Value at pin |
| --- | --- |
| `GUNNCHAI_DIGITAL_PRODUCT_CAPABILITY_PASS` | `true` |
| `GUNNCHAI_APP_PRODUCT_COMPLETE` | `false` |
| `GUNNCHAI_FRONTIER_PRODUCT_PARITY` | `false` |
| `HUMAN_E6` | `false` |
| `NANO_FALLBACK_ONLY` | `true` |

Product UI must not promote PARTIAL/OPEN surfaces to COMPLETE. When the sibling
runtime is unavailable, device-os uses deterministic local templates (not a
frontier quality claim).

## Verification

```bash
# Always safe — validates pin file + schema (runs in main CI)
PYTHONPATH=. pytest tests/test_gunnchai_compat_contract.py -q

# Optional — sibling checkout at pinned SHA
PYTHONPATH=. python3 scripts/verify_gunnchai_sibling_contract.py \
  --gunnchai-repo ../gunnchAI3k
```

Sibling verification is **optional** (`.github/workflows/gunnchai-sibling-compat.yml`,
`workflow_dispatch` only). It does not gate device-os CI green.

## Related (not duplicated)

- Supervisor-ready #121: service-continuity profiles (orthogonal)
- PRODUCT-USE RC-002 honesty consume (`gunnchai_honesty.py`) — legacy #37 matrix;
  this contract supersedes the **pairing pin** for residual closure Phase 4
- device-os #103: NONE_TO_PORT — do not merge
