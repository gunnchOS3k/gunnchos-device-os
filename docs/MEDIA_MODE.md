# Media Mode

Media Mode is GunnchOS's dedicated full-screen experience for streaming video, education lectures, music/audio, and local media playback.

## Why it exists

For students without multiple devices, media is not only entertainment — YouTube is often a classroom, lecture recordings support homework, and creators use video platforms for research and publishing. Media Mode makes streaming a **first-class OS capability**, separate from Campus shortcuts and Game Mode.

## Media Mode vs Campus Mode vs Game Mode

| Mode | Priority | Content |
|------|----------|---------|
| **Campus Mode** | School & productivity | Shortcuts to media; not full-screen streaming UX |
| **Media Mode** | Playback & streaming | YouTube, Netflix, Hulu, local media, diagnostics |
| **Game Mode** | Performance & games | Anime Aggressors, Foot Racing, Earth Species only |

Game Mode does **not** become a streaming mode. Media state does not corrupt game sessions — modes are isolated shells.

## What's in Media Mode (Phase 1 prototype)

- Full-screen media launcher with touch/controller labels
- YouTube, Netflix, Hulu (browser route prototypes)
- Local Media, Lecture Video, Music & Audio placeholders
- Future streaming services placeholder
- Network quality checklist (mock)
- Battery/playback profiles
- Audio output placeholder
- Captions/subtitles preference
- External display / HDCP warning
- Guardian/school/library restriction summary
- DRM disclaimers on Netflix/Hulu cards

## Phase 4E certification readiness (prototype)

Phase 4E adds a **readiness package** — not certification. Track per-service status in:

- [streaming_certification/SERVICE_CERTIFICATION_TRACKER.yaml](../streaming_certification/SERVICE_CERTIFICATION_TRACKER.yaml)
- [streaming_certification/STREAMING_COMPATIBILITY_MATRIX.md](../streaming_certification/STREAMING_COMPATIBILITY_MATRIX.md)
- [streaming_certification/CDM_READINESS_CHECKLIST.md](../streaming_certification/CDM_READINESS_CHECKLIST.md)
- [streaming_certification/HDCP_EXTERNAL_DISPLAY_CHECKLIST.md](../streaming_certification/HDCP_EXTERNAL_DISPLAY_CHECKLIST.md)
- [PHASE4E_STREAMING_CDM_CERTIFICATION.md](PHASE4E_STREAMING_CDM_CERTIFICATION.md)

No service may be marked `certified` in the tracker without an on-disk evidence path.

## Claim boundary (required reading)

GunnchOS does **not** claim:

- Official Netflix, Hulu, Disney+, or other streaming certification
- DRM circumvention or bypass
- Guaranteed HDCP external display playback
- Guaranteed Widevine/CDM availability on all hardware

Honest labels used in the UI:

- "Browser route prototype"
- "DRM/CDM support required"
- "HDCP may be required for external display"
- "Service certification not claimed"
- "Playback quality depends on browser, hardware, network, codec, DRM, and service policy"

## Policy rules

| Context | YouTube | Netflix/Hulu | Local media |
|---------|---------|--------------|-------------|
| Media Mode | Allowed | Allowed | Allowed |
| School Mode | Policy-dependent | Blocked | Lecture allowed |
| Guardian Mode | Gated | Blocked | Allowed |
| Library Mode | Policy-dependent | Blocked | Lecture allowed |
| Offline Mode | Blocked | Blocked | Allowed |

Media Mode blocks Steam and VS Code by default.

## Navigation

Enter from Campus dock → **Media Mode** tile. Exit returns to Campus without affecting Game Mode state.
