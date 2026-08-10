# WP-003 / WP-003R.1 Golden Journey Defect Backlog

## Independent VP-003R / VP-003R.1 (accepted main tip)

- Prior Independent digital residuals G06/G07/G08 closed on tip ⊆ main (#85)
- WP-003R.1: tip `645d31a` ⊆ main `801b332` (#88). **GJ-DEFECT-005 = CLOSED_INDEPENDENT_PASS** (privileged netns+packet transfer + Pulse/ALSA audio lifecycle; logical FALLBACK_ONLY ≠ E4)
- Remaining physical/human PARTIALs unchanged

## Remaining PARTIAL by design (do not fake-close)

| ID | Journey | Cap |
|---|---|---|
| VP003-S2-G04-PHYSICAL-DOCK | GOLDEN-04 | PHYSICAL_PENDING (E5) |
| VP003-S2-G06-PHYSICAL-DUAL | GOLDEN-06 | PHYSICAL_PENDING (E5) |
| VP003-S2-G07-PHYSICAL-RING | GOLDEN-07 | PHYSICAL_PENDING (E5) |
| VP003-S2-G08-CITATION-HUMAN | GOLDEN-08 | HUMAN_VALIDATION_PENDING (E6) |

## GJ-DEFECT-005 (WP-003R.1)

- Status: **`CLOSED_INDEPENDENT_PASS`** (VP-003R.1 Independent; tip `645d31a` / main `801b332`)
- Privileged CI job: netns+veth **actual packet transfer** + PipeWire/Pulse/ALSA virtual audio lifecycle
- Unprivileged path: `FALLBACK_ONLY` / `NOT_E4_REFERENCE_PROOF` (available, not counted as E4 G04 reference)
- Evidence: `quality/golden_journeys/verifier/VP-003R.1-RESULT.json`

Honesty: `frontier_parity_claimed=false`. No fabricated competitor scores.
