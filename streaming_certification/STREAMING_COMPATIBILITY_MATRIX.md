# Streaming Compatibility Matrix

**Phase 4E — readiness tracking only**  
**Last updated:** 2026-07-02  
**Claim boundary:** No official streaming service certification is claimed. See [SERVICE_CERTIFICATION_TRACKER.yaml](SERVICE_CERTIFICATION_TRACKER.yaml).

---

## Legend

| Symbol | Meaning |
|--------|---------|
| ✓ | Implemented or validated with evidence |
| ~ | Prototype / partial / readiness only |
| — | Not started |
| DRM | Requires Widevine or service-specific CDM |
| HDCP | May block external display without HDCP handshake |

---

## Service matrix

| Service | Media Mode route | Browser path | DRM/CDM | HDCP ext. display | Launcher status | Certification status | Evidence |
|---------|------------------|--------------|---------|-------------------|-----------------|----------------------|----------|
| YouTube | ✓ external tab | Chromium HTML5/MSE | Optional (premium) | No | browser_route_prototype | browser_route_prototype | UI + `media_apps.py` |
| Netflix | ✓ external tab + disclaimer | Chromium + Widevine | **Required** | Yes | browser_route_prototype | readiness_prototype | [CDM_READINESS_CHECKLIST.md](CDM_READINESS_CHECKLIST.md) |
| Hulu | ✓ external tab + disclaimer | Chromium + Widevine | **Required** | Yes | browser_route_prototype | readiness_prototype | [CDM_READINESS_CHECKLIST.md](CDM_READINESS_CHECKLIST.md) |
| Disney+ | — future placeholder | Chromium + Widevine | **Required** | Yes | future_placeholder | not_started | — |
| Max | — future placeholder | Chromium + Widevine | **Required** | Yes | future_placeholder | not_started | — |
| Prime Video | — future placeholder | Chromium + Widevine | **Required** | Yes | future_placeholder | not_started | — |
| Peacock | — future placeholder | Chromium + Widevine | **Required** | Yes | future_placeholder | not_started | — |
| Paramount+ | — future placeholder | Chromium + Widevine | **Required** | Yes | future_placeholder | not_started | — |
| Crunchyroll | — future placeholder | Chromium + Widevine | **Required** | Yes | future_placeholder | not_started | — |
| Twitch | — future placeholder | Chromium HTML5/MSE | Usually none | No | future_placeholder | not_started | — |
| Local media | ✓ in-shell player | HTML5 `<video>`/`<audio>` | **No** | No | browser_route_prototype | browser_route_prototype | [PHASE2C_LOCAL_MEDIA_PLAYER.md](../docs/PHASE2C_LOCAL_MEDIA_PLAYER.md) |

---

## Codec and stack expectations (target)

| Capability | Target | GunnchOS today |
|------------|--------|----------------|
| H.264 hardware decode | Required for streaming efficiency | Not validated on reference hardware |
| VP9 / AV1 | Preferred for YouTube/Netflix tiers | Not validated |
| MSE / EME | Required for DRM services | Not integrated |
| Widevine CDM | Required for Netflix/Hulu/Disney+ class services | **Not integrated** |
| HDCP 1.4/2.2 on HDMI/USB-C | External display policy dependent | Not validated |
| Audio routing / Bluetooth | Target OS feature | Placeholder in Media Mode |
| Captions | Service + OS accessibility path | Not validated end-to-end |

---

## Mode policy interaction

| Service | Media Mode | School | Guardian | Library | Offline |
|---------|------------|--------|----------|---------|---------|
| YouTube | Allowed | Policy-dependent | Gated | Policy-dependent | Blocked |
| Netflix / Hulu | Allowed (disclaimer) | Blocked | Blocked | Blocked | Blocked |
| Future DRM services | Not routed | Blocked | Blocked | Blocked | Blocked |
| Local media | Allowed | Lecture allowed | Allowed | Lecture allowed | Allowed |

---

## Beta gate rule

`streaming_certification` remains **prototype** until:

1. Widevine-capable browser path is integrated and tested on reference hardware/OS image.
2. Per-service playback smoke tests are recorded with evidence paths in the tracker.
3. HDCP external-display behavior is documented with test logs.
4. No service is marked `certified` without partner letter or audited test report.

---

## Related

- [CDM_READINESS_CHECKLIST.md](CDM_READINESS_CHECKLIST.md)
- [HDCP_EXTERNAL_DISPLAY_CHECKLIST.md](HDCP_EXTERNAL_DISPLAY_CHECKLIST.md)
- [SERVICE_CERTIFICATION_TRACKER.yaml](SERVICE_CERTIFICATION_TRACKER.yaml)
- [PHASE4E_STREAMING_CDM_CERTIFICATION.md](../docs/PHASE4E_STREAMING_CDM_CERTIFICATION.md)
