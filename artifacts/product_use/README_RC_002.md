# PRODUCT-USE-RC-002

Successor to PRODUCT-USE-RC-001 (#115 merge ≠ complete). Branch: `stream/product-use-rc-002`.

## Hard gates

- Host free space: required ≥25 GiB, preferred ≥40 GiB (supersedes prefer-12).
- Cursor never merges.
- No WP-001 / PROFILE README / GAME-RC-003 / AI-003 / field-kit aggregate in this stream.

## Owner SHA pins

See `OWNER_SHA_PINS.json` (refreshed at stream start).

## WAIKE six-course ingest

Exact owner IDs from waike-research-ops #43+#44:

- `GENERAL_IT`
- `COMPUTER_NETWORKING`
- `CYBERSECURITY`
- `SOFTWARE_BUILDER`
- `HARDWARE_ENGINEERING` (+ `EMBEDDED_PROTOTYPING` track)
- `PM_AGILE_LSS`

Active store version must be the six-course pack (`owner-cabe2a4c425f` or newer digest). Stale three-course pack is not active. Curriculum is not re-authored in device-os.

## gunnchAI honesty (#34)

Consumed into `GUNNCHAI_HONESTY_CONSUMED.json`: **7 COMPLETE / 3 PARTIAL / 6 OPEN**.

Product UI must not claim COMPLETE for PARTIAL/OPEN. Persona-safe COMPLETE capabilities: Local Fast, Projects/memory, source-grounded, Socratic, tool permission, artifacts.

## Artifacts

| Path | Meaning |
|------|---------|
| `HOST_STORAGE_PREFLIGHT.json` | 25/40 GiB gate |
| `OWNER_SHA_PINS.json` | Accepted-main pins |
| `WAIKE_SIX_COURSE_INGEST.json` | Signed import + rollback |
| `GUNNCHAI_HONESTY_CONSUMED.json` | AI matrix consume |
| `PRODUCT_USE_RC_002_STATUS.json` | Stream status |
| `PERSONA_JOURNEY_TABLE.json` | G11–G15 honesty table |
| `journeys/` | Guest evidence |

## Tokens

All `*_DIGITAL_PICKUP_AND_USE_READY` tokens stay false unless independently reproducible later with S1=0.
