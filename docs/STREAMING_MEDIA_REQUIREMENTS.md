# Streaming Media Requirements

GunnchOS must support streaming media as a first-class OS experience for learners, creators, workers, and gamers.

## Required initial routes

- YouTube
- Netflix
- Hulu
- Local media files
- School lecture video
- Music/audio (future)

## Future routes (not Phase 1)

Disney+, Max, Prime Video, Peacock, Paramount+, Crunchyroll, Twitch, Spotify, Apple Music

## Technical requirements (target stack)

- Chromium-compatible browser path
- HTML5 video, MSE, EME where legally available
- Hardware video decode (H.264, VP9, AV1)
- Widevine-capable browser path where legally available
- HDCP-aware external display handling
- Network diagnostics, audio routing, Bluetooth audio, captions

## DRM and service compatibility

**GunnchOS must not claim official compatibility** with DRM-protected services until real browser, DRM, CDM, HDCP, and service testing is complete.

Required statements:

1. DRM circumvention is not supported.
2. Playback depends on browser, hardware, network, codec, DRM, and service policy.
3. External display may require HDCP.
4. Some services may restrict resolution on Linux or unsupported devices.
5. Service certification is a future release requirement.

## Mode restrictions

See [MEDIA_MODE.md](MEDIA_MODE.md) for School, Guardian, Library, and Offline rules.

## Phase 4E certification readiness (prototype)

| Artifact | Purpose |
|----------|---------|
| [SERVICE_CERTIFICATION_TRACKER.yaml](../streaming_certification/SERVICE_CERTIFICATION_TRACKER.yaml) | Per-service DRM, HDCP, and certification evidence tracking |
| [STREAMING_COMPATIBILITY_MATRIX.md](../streaming_certification/STREAMING_COMPATIBILITY_MATRIX.md) | Service × codec × mode matrix |
| [CDM_READINESS_CHECKLIST.md](../streaming_certification/CDM_READINESS_CHECKLIST.md) | Widevine/EME integration prerequisites |
| [HDCP_EXTERNAL_DISPLAY_CHECKLIST.md](../streaming_certification/HDCP_EXTERNAL_DISPLAY_CHECKLIST.md) | External display test plan |
| [PHASE4E_STREAMING_CDM_CERTIFICATION.md](PHASE4E_STREAMING_CDM_CERTIFICATION.md) | Phase summary and validation commands |

Validator: `python3 scripts/validate_streaming_certification_tracker.py`

## Phase 1 implementation status

| Requirement | Phase 1 | Phase 4E |
|-------------|---------|----------|
| Media Mode shell | Prototype UI | Prototype UI |
| YouTube/Netflix/Hulu cards | Browser route prototype | Browser route prototype |
| Local media | HTML5 prototype (Phase 2C) | Tracked separately from DRM in tracker |
| Real browser/DRM/CDM | Not implemented | Readiness checklists only |
| Service certification | Not claimed | Tracker + validator; still not claimed |
| Policy tests | Implemented | Implemented |
