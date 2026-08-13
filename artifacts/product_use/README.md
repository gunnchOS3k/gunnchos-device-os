# PRODUCT-USE-RC-001 (bounded DRAFT)

Pickup-and-use journeys on Device Lab profiles with **accepted-main** apps/AI/WAIKE.

## WAIKE ingest (owner = waike-research-ops)

```bash
PYTHONPATH=.:src python3 scripts/product_use_ingest_waike43.py \
  --owner-root ../waike-research-ops
```

- Reads `ingest/learner` + `ingest/teacher` from owner checkout (accepted #43).
- Builds a **signed DEV_TEST** versioned package under `artifacts/product_use/waike_store/`.
- Learner projection strips instructor keys; teacher view retains them.
- Supports activate / rollback via `WaikeOwnerPackageStore`.
- **Does not re-author curriculum** in device-os.

## Personas

See `gunnchos_device_os/product_use/personas.py` (G11–G15). Tokens stay false until independently reproducible guest evidence exists.

## Honest limits

- `REAL_TEACHER_E6=false`
- `FOUR_GAME_ACCEPTED_MAIN_RC=false` until Edmund merges Beat Link #20
- `VISUAL_MODEL_REVIEW=UNAVAILABLE` when no pixel inspect
- No HTML surrogate / host masquerade as final PASS
