# VXP Test Matrix

| Test | Command | Authority |
|---|---|---|
| Unit/a11y shell | `cd apps/gunnch_shell && npm test` | Digital |
| Typecheck | `npm run typecheck` | Digital |
| Build | `npm run build` | Digital |
| Screenshot fixtures | `npm run vxp:capture` | VISUAL_FIXTURE_NOT_PROVIDER_PROOF |
| Capsule | `make android-capsule` | Build artifact |
| Pixel visual | ADB capture only if safe | Physical — else PENDING |
