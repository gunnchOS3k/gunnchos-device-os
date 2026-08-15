# PRODUCT-USE-RC-002

Successor to PRODUCT-USE-RC-001 (#115 merge ≠ complete). Branch: `stream/product-use-rc-002`. PR: #116 only.

## Hard gates

- Host free space: required ≥25 GiB, preferred ≥40 GiB (supersedes prefer-12).
- Cursor never merges.
- No WP-001 / PROFILE README / second Product-Use PR / field-kit aggregate in this stream.

## Owner SHA pins

See `OWNER_SHA_PINS.json` (refresh after live GitHub accepted mains; do not restart QEMU solely for SHA delta).

## WAIKE twelve-course ingest

Exact owner IDs from waike-research-ops #46 (post-#46 tip / #47 mastery on main):

- `GENERAL_IT`
- `COMPUTER_NETWORKING`
- `CYBERSECURITY`
- `SOFTWARE_BUILDER`
- `HARDWARE_ENGINEERING` (+ `EMBEDDED_PROTOTYPING` track)
- `PM_AGILE_LSS`
- `AI_ML_EDGE`
- `DATA_VIZ_BI`
- `CLOUD_DEVOPS`
- `WIRELESS_6G`
- `ROBOTICS_CONTROL`
- `GAME_DEV_INTERACTIVE`

Active store version must be the twelve-course pack. Stale nine-/six-/three-course packs are not active. Curriculum is not re-authored in device-os.

## gunnchAI honesty (#37 tip; matrix from #35)

Consumed into `GUNNCHAI_HONESTY_CONSUMED.json`: **9 COMPLETE / 1 PARTIAL / 6 OPEN** + `#37` mastery sidecar.
**Do not consume unmerged gunnchAI #36.**

Product UI must not claim COMPLETE for PARTIAL/OPEN. Persona-safe COMPLETE capabilities include Local Fast, Projects/memory, source-grounded, Socratic, tool permission, artifacts, deep research, coding DRAFT PR. Vision/OCR remains PARTIAL.

## Artifacts

| Path | Meaning |
|------|---------|
| `HOST_STORAGE_PREFLIGHT.json` | 25/40 GiB gate |
| `OWNER_SHA_PINS.json` | Accepted-main pins |
| `OWNER_PACK_REFRESH.json` | Old/new SHA + versioned install/rollback |
| `WAIKE_SIX_COURSE_INGEST.json` | Signed import + rollback (filename retained; payload is twelve-course) |
| `GUNNCHAI_HONESTY_CONSUMED.json` | AI matrix + mastery consume |
| `PRODUCT_USE_RC_002_STATUS.json` | Stream status |
| `PERSONA_JOURNEY_TABLE.json` | G11–G15 honesty table |
| `journeys/` | Guest evidence |
| `RECOVERY_RECORD.json` | Only if 3h ceiling without sentinel |

## Tokens

All `*_DIGITAL_PICKUP_AND_USE_READY` tokens stay false unless independently reproducible later with S1=0.
