# PLATFORM-001 → field-kit V2 contribution note

Short handoff for `gunnchos-7gc-ai-ran-field-kit` Charter V2 atomic register.
Source tip lives on device-os DRAFT PR for PLATFORM-001 (not merged by Cursor).

## Token honesty (post shell↔SDK remediation)

| Token | Value | Status |
|---|---|---|
| `CREATOR_FIRST_PARTY_APP_D5_D6_PASS` | **true** | PASS — lifecycle + companion bridge sandbox I/O |
| `WAIKE_FIRST_PARTY_APP_D5_D6_PASS` | **true** | PASS — same |
| `GUNNCHAI_FIRST_PARTY_APP_D5_D6_PASS` | **true** | PASS — Ask → SDK_SANDBOX_MEMORY (no DISCONNECTED_PREVIEW success) |

Supporting:
- `platform_lifecycle_d5` / `cross_service_d6` earned on `sdk/apps/*` (not `sdk/examples/*`)
- `companion_shell_wiring.ok=true` via `prove_companion_shell_wiring`
- `VISUAL_MODEL_REVIEW=UNAVAILABLE` (residual OPEN, **non-blocking** for platform integration PASS)
- `HUMAN_E6=NOT_EARNED`
- `PRODUCTION_RELEASE_CLAIMED=false`
- Curriculum / frontier model quality remain false

Claim boundary: FIRST_PARTY_APP_D5_D6_PASS here means **platform integration depth** (package lifecycle + shell↔sandbox I/O + Ask continuity), not visual polish, not HUMAN_E6, not curriculum/model quality.

## PLATFORM-related atomic register (propose for field-kit V2)

| Atomic ID (proposed) | Title | Status after remediation |
|---|---|---|
| `PLATFORM-UX-CREATOR-SHELL-01` | Creator companion shell wired to sandbox runtime I/O | **CLOSED digitally** (bridge `/api/creator/run`) |
| `PLATFORM-UX-WAIKE-LEARNER-01` | WAIKE learner UI durable progress via SDK | **CLOSED digitally** (`/api/waike/start`) |
| `PLATFORM-UX-WAIKE-CONTENT-01` | WAIKE full curriculum authorship | Still OPEN / out of scope |
| `PLATFORM-UX-GUNNCHAI-CONTINUITY-01` | Tutor shell ↔ SDK runtime state continuity | **CLOSED digitally** (`/api/gunnchai/ask` → SDK_SANDBOX_MEMORY) |
| `PLATFORM-EXP-VISUAL-INSPECT-01` | Rendered visual inspect for Creator/WAIKE/gunnchAI | Still OPEN (`VISUAL_MODEL_REVIEW=UNAVAILABLE`) — non-blocking residual |
| `PLATFORM-HUMAN-E6-01` | Human comprehension / student validation | Still OPEN / NOT_EARNED |
| `PLATFORM-DEVICELAB-FIRSTPARTY-01` | Device Lab LIVE visual + ring mutation on these apps | Distinct; do not merge stale #103 blindly |
| `OS-PLATFORM-001` | Unified user identity (charter req) | Distinct; not satisfied by app-depth dogfood |

## Explicit non-OPEN misreads to avoid

- Do not treat `sdk/examples/*` stubs as product evidence.
- Do not equate platform-integration PASS with visual polish or HUMAN_E6.
- Do not set `HUMAN_E6` / `STUDENT_VALIDATED` from this packet.

## Evidence paths

- `artifacts/platform001/PLATFORM001_RESULT.json`
- `artifacts/platform001/GAP_REGISTER.json`
- `artifacts/platform001/REMEDIATION_SHELL_SDK_WIRING.json`
- `artifacts/platform001/VP_PLATFORM001_INDEPENDENT_RESULT.json` (prior verifier demotion retained for history)
- `artifacts/experience_review/{creator_studio,waike_learning,gunnchai_tutor}/`
- `gunnchos_device_os/first_party_apps/companion_bridge.py`
- `scripts/platform001_companion_bridge.py`
- `scripts/platform001_first_party_dogfood.py`
