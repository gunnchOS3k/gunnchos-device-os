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

## Phase 1 implementation status

| Requirement | Phase 1 |
|-------------|---------|
| Media Mode shell | Prototype UI |
| YouTube/Netflix/Hulu cards | Browser route prototype |
| Local media | Placeholder |
| Real browser/DRM/CDM | Not implemented |
| Service certification | Not claimed |
| Policy tests | Implemented |
