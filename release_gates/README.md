# Release Gates

**Status:** gate model documented · **GA release not met**

Release gates define evidence required before stage-specific claims. All gates use honest status values — **not shipping yet**.

## Documents

| Document | Purpose |
|----------|---------|
| [RELEASE_GATE_MATRIX.md](RELEASE_GATE_MATRIX.md) | Master status table |
| [RELEASE_EVIDENCE_MATRIX.md](RELEASE_EVIDENCE_MATRIX.md) | Evidence artifact cross-reference |
| [RELEASE_SIGNOFF_TEMPLATE.md](RELEASE_SIGNOFF_TEMPLATE.md) | Sign-off form |
| [RELEASE_RISK_REGISTER.md](RELEASE_RISK_REGISTER.md) | Release risks |
| [RELEASE_BLOCKERS.md](RELEASE_BLOCKERS.md) | Active blockers |

## Gate definitions

| Gate | Document |
|------|----------|
| Alpha | [ALPHA_GATE.md](ALPHA_GATE.md) |
| Beta | [BETA_GATE.md](BETA_GATE.md) |
| Release candidate | [RELEASE_CANDIDATE_GATE.md](RELEASE_CANDIDATE_GATE.md) |
| GA release | [GA_RELEASE_GATE.md](GA_RELEASE_GATE.md) |
| Field pilot | [FIELD_PILOT_GATE.md](FIELD_PILOT_GATE.md) |
| Production release | [PRODUCTION_RELEASE_GATE.md](PRODUCTION_RELEASE_GATE.md) |

## Valid status values

`not_started` · `planned` · `in_progress` · `evidence_exists` · `validated` · `blocked` · `passed`

## Validation

```bash
python scripts/validate_release_gates.py
```

## Claim boundary

Passing a gate requires linked evidence. This package does **not** claim GA release or finished shipping OS.
