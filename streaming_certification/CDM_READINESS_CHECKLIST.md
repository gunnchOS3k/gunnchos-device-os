# CDM Readiness Checklist

**Phase 4E — Widevine / EME integration readiness**  
**Status:** Readiness package only — **CDM not integrated**  
**Last updated:** 2026-07-02

GunnchOS does **not** claim Widevine, PlayReady, or FairPlay certification. This checklist defines what must be true before DRM streaming services can be honestly tested or certified.

---

## Claim boundary (required)

- DRM circumvention is **not** supported.
- Service certification is **not** claimed until partner approval or audited evidence exists.
- Browser route prototypes that open Netflix/Hulu in an external tab are **not** CDM validation.

---

## 1. Legal and licensing

| Item | Status | Evidence |
|------|--------|----------|
| Widevine / CDM distribution agreement path identified | Not started | — |
| No circumvention tooling in repo | ✓ | Code + doc audit |
| Third-party CDM redistribution policy documented | Not started | — |
| Service ToS compatibility reviewed | Not started | — |

---

## 2. Browser and EME stack

| Item | Status | Notes |
|------|--------|-------|
| Chromium-compatible browser selected for OS image | Partial | External tab prototype only |
| `navigator.requestMediaKeySystemAccess` available | Not tested | Requires integrated browser |
| Widevine L3 (software) path documented | Not started | Minimum for Linux-class devices |
| Widevine L1 (hardware) path evaluated per SKU | Not started | May require OEM partnership |
| MSE pipeline validated for adaptive streaming | Not started | — |
| User-agent / platform string policy for services | Not started | Some services restrict Linux |

---

## 3. OS integration

| Item | Status | Notes |
|------|--------|-------|
| CDM loaded in sandboxed browser process | Not started | — |
| CDM updates tied to OS/browser update channel | Not started | — |
| Secure storage for session/license handles | Not started | — |
| Crash isolation — CDM failure does not brick shell | Not started | — |
| Telemetry excludes license keys / content URLs | Not started | Privacy review required |

---

## 4. Per-service DRM requirements (tracker summary)

| Service | DRM required | Current GunnchOS status |
|---------|--------------|-------------------------|
| YouTube | Optional (premium/rental) | Browser prototype |
| Netflix | **Yes** (Widevine) | Disclaimer only |
| Hulu | **Yes** (Widevine) | Disclaimer only |
| Disney+ / Max / Prime / Peacock / Paramount+ / Crunchyroll | **Yes** | Future route |
| Twitch | Usually no | Future route |
| Local media | **No** | HTML5 prototype — separate path |

---

## 5. Test plan (execute when CDM integrated)

| Test | Pass criteria | Evidence file |
|------|---------------|---------------|
| EME capability probe | `requestMediaKeySystemAccess('com.widevine.alpha')` succeeds | `results/streaming/cdm_capability.json` |
| Netflix playback smoke | Licensed test account plays 1080p (or documented max) | `results/streaming/netflix_smoke.md` |
| Hulu playback smoke | Licensed test account plays content | `results/streaming/hulu_smoke.md` |
| License renewal | 2+ hour session without fatal CDM error | Session log |
| Airplane mode recovery | Graceful error, no shell crash | UI capture |
| CDM update rollback | Documented recovery | Runbook |

---

## 6. Sign-off (blocked until evidence)

- [ ] Engineering: EME/Widevine path integrated on reference image
- [ ] Security: No license key leakage in logs
- [ ] Legal: CDM distribution path approved
- [ ] QA: Per-service smoke tests filed with evidence paths in tracker
- [ ] Product: No UI copy claims certification before sign-off

**Owner:** Media platform + OS browser integration

---

## Related

- [SERVICE_CERTIFICATION_TRACKER.yaml](SERVICE_CERTIFICATION_TRACKER.yaml)
- [STREAMING_COMPATIBILITY_MATRIX.md](STREAMING_COMPATIBILITY_MATRIX.md)
- [HDCP_EXTERNAL_DISPLAY_CHECKLIST.md](HDCP_EXTERNAL_DISPLAY_CHECKLIST.md)
