# Creator Studio — experience review summary

- Platform lifecycle D5/D6 dogfood: earned on `sdk/apps/creator_studio` (not examples)
- Companion shell: wired to `/api/creator/run` → `first_party_apps.creator_studio.run_creator_studio` sandbox I/O
- Fail-closed when bridge down (`RUNTIME_UNAVAILABLE`); no mock terminal success
- S2 residual: `VISUAL_MODEL_REVIEW=UNAVAILABLE` (non-blocking); prototype polish remains
- FIRST_PARTY_APP_D5_D6_PASS: true (platform integration depth only)
