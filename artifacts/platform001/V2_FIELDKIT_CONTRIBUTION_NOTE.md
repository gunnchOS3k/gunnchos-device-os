# PLATFORM-001 → field-kit V2 contribution note

Short handoff for `gunnchos-7gc-ai-ran-field-kit` Charter V2 atomic register.
Source tip lives on device-os DRAFT PR for PLATFORM-001 (not merged by Cursor).

## Earned digital tokens (device-os evidence)

- `CREATOR_FIRST_PARTY_APP_D5_D6_PASS` — see `artifacts/platform001/PLATFORM001_RESULT.json`
- `WAIKE_FIRST_PARTY_APP_D5_D6_PASS`
- `GUNNCHAI_FIRST_PARTY_APP_D5_D6_PASS`

Claim boundary: gunnchSDK dogfood + owner-function runtime + cross-service binding.
Not HUMAN_E6, not full WAIKE curriculum, not frontier AI quality, not Device Lab visual PASS.

## PLATFORM-related atomic OPEN requirements (propose for field-kit V2)

| Atomic ID (proposed) | Title | Why still OPEN |
|---|---|---|
| `PLATFORM-UX-CREATOR-SHELL-01` | Creator companion shell wired to sandbox runtime I/O | HTML run/build still simulated; S2 trust gap |
| `PLATFORM-UX-WAIKE-LEARNER-01` | WAIKE learner UI replaces JSON progress dump | Progress/JSON panel is developer-dashboard-like |
| `PLATFORM-UX-WAIKE-CONTENT-01` | WAIKE lesson body + worked example surface | Pack IDs only; curriculum depth out of PLATFORM-001 scope but UX still OPEN |
| `PLATFORM-UX-GUNNCHAI-CONTINUITY-01` | Tutor shell ↔ SDK runtime state continuity | Browser Ask is disconnected preview |
| `PLATFORM-EXP-VISUAL-INSPECT-01` | Rendered visual inspect for Creator/WAIKE/gunnchAI | Experience visual status UNAVAILABLE |
| `PLATFORM-HUMAN-E6-01` | Human comprehension / student validation | HUMAN_E6 not earned by AI review |
| `PLATFORM-DEVICELAB-FIRSTPARTY-01` | Device Lab LIVE visual + ring mutation on these apps | Distinct from SDK dogfood; needs accepted-main Device Lab packet (do not merge stale #103 blindly) |
| `OS-PLATFORM-001` | Unified user identity (charter req) | Distinct requirement; not satisfied by app-depth dogfood |

## Explicit non-OPEN misreads to avoid

- Do not treat `sdk/examples/*` stubs as product evidence.
- Do not collapse “app integration PASS” into “WAIKE curriculum complete” or “gunnchAI model quality PASS”.
- Do not set `HUMAN_E6` / `STUDENT_VALIDATED` from this packet.

## Evidence paths

- `artifacts/platform001/PLATFORM001_RESULT.json`
- `artifacts/platform001/GAP_REGISTER.json`
- `artifacts/experience_review/{creator_studio,waike_learning,gunnchai_tutor}/`
