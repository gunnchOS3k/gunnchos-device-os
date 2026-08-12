# PLATFORM-001 → field-kit V2 contribution note

Short handoff for `gunnchos-7gc-ai-ran-field-kit` Charter V2 atomic register.
Source tip lives on device-os DRAFT PR for PLATFORM-001 (not merged by Cursor).

## Token honesty (independent verifier remediation)

| Token | Value | Status |
|---|---|---|
| `CREATOR_FIRST_PARTY_APP_D5_D6_PASS` | **false** | PARTIAL — platform lifecycle earned; S2 OPEN blocks PASS |
| `WAIKE_FIRST_PARTY_APP_D5_D6_PASS` | **false** | PARTIAL — same |
| `GUNNCHAI_FIRST_PARTY_APP_D5_D6_PASS` | **false** | PARTIAL — same |

Supporting (not product PASS):
- `platform_lifecycle_d5` / `cross_service_d6` earned on `sdk/apps/*` (not `sdk/examples/*`)
- `VISUAL_MODEL_REVIEW=UNAVAILABLE`
- `HUMAN_E6=NOT_EARNED`
- `PRODUCTION_RELEASE_CLAIMED=false`
- Curriculum / frontier model quality remain false

Claim boundary: gunnchSDK dogfood + owner-function runtime + cross-service binding may be earned while FIRST_PARTY_APP_D5_D6_PASS stays demoted until companion shell↔SDK wiring and visual inspect S2 close.

## PLATFORM-related atomic OPEN requirements (propose for field-kit V2)

| Atomic ID (proposed) | Title | Why still OPEN |
|---|---|---|
| `PLATFORM-UX-CREATOR-SHELL-01` | Creator companion shell wired to sandbox runtime I/O | Honest preview only; not wired — **blocks token PASS** |
| `PLATFORM-UX-WAIKE-LEARNER-01` | WAIKE learner UI durable progress via SDK | Cards remidiated; durable wiring still OPEN |
| `PLATFORM-UX-WAIKE-CONTENT-01` | WAIKE full curriculum authorship | Lesson body surface added; curriculum quality still out of scope |
| `PLATFORM-UX-GUNNCHAI-CONTINUITY-01` | Tutor shell ↔ SDK runtime state continuity | Browser Ask is DISCONNECTED_PREVIEW — **blocks token PASS** |
| `PLATFORM-EXP-VISUAL-INSPECT-01` | Rendered visual inspect for Creator/WAIKE/gunnchAI | `VISUAL_MODEL_REVIEW=UNAVAILABLE` — **blocks token PASS** |
| `PLATFORM-HUMAN-E6-01` | Human comprehension / student validation | HUMAN_E6 not earned by AI review |
| `PLATFORM-DEVICELAB-FIRSTPARTY-01` | Device Lab LIVE visual + ring mutation on these apps | Distinct from SDK dogfood; do not merge stale #103 blindly |
| `OS-PLATFORM-001` | Unified user identity (charter req) | Distinct requirement; not satisfied by app-depth dogfood |

## Explicit non-OPEN misreads to avoid

- Do not treat `sdk/examples/*` stubs as product evidence.
- Do not collapse “SDK lifecycle dogfood” into “FIRST_PARTY_APP_D5_D6_PASS”.
- Do not set `HUMAN_E6` / `STUDENT_VALIDATED` from this packet.

## Evidence paths

- `artifacts/platform001/PLATFORM001_RESULT.json`
- `artifacts/platform001/GAP_REGISTER.json`
- `artifacts/platform001/VP_PLATFORM001_INDEPENDENT_RESULT.json`
- `artifacts/experience_review/{creator_studio,waike_learning,gunnchai_tutor}/`
