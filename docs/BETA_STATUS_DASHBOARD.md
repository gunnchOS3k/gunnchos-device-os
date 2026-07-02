# Beta Status Dashboard

Machine-readable beta progress: [`beta_gate/beta_gate_status.yaml`](../beta_gate/beta_gate_status.yaml)

## Validate

```bash
python3 scripts/validate_beta_gate.py
```

## Rules

- `validated` status requires `evidence_paths`
- `beta_ready: true` forbidden while any P0 item is `missing` or `prototype`
- Current `beta_ready: false` — beta not claimed

## Summary (Phase 2G baseline on main)

| Area | Status |
|------|--------|
| CI + contract | validated |
| File manager + notes | implemented |
| Browser/PWA | missing (2B pending) |
| Local media | missing (2C pending) |
| Game launch + Anime Aggressors | missing (2D/2E pending) |
| Bootable image track | missing (2F pending) |
| Hardware evidence | missing |

Update `beta_gate_status.yaml` as PRs merge toward beta candidate.
