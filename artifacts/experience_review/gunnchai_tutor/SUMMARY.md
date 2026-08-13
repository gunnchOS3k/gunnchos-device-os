# gunnchAI Tutor — experience review summary

- Platform lifecycle D5/D6 dogfood: earned on `sdk/apps/gunnchai_tutor`
- Browser Ask: wired to `/api/gunnchai/ask` → `run_gunnchai_tutor` with `CONTINUITY: SDK_SANDBOX_MEMORY`
- DISCONNECTED_PREVIEW success path removed; fail-closed `RUNTIME_UNAVAILABLE` when bridge down
- S2 residual: `VISUAL_MODEL_REVIEW=UNAVAILABLE` (non-blocking); frontier model quality not claimed
- FIRST_PARTY_APP_D5_D6_PASS: true (platform integration depth only); HUMAN_E6 not earned
