# HDCP External Display Checklist

**Phase 4E — external display / HDCP readiness**  
**Status:** Readiness package only — **HDCP not validated**  
**Last updated:** 2026-07-02

DRM-protected streaming services may refuse playback, downgrade resolution, or block output when an external display does not support HDCP. GunnchOS must document and test this honestly before claiming external-display streaming support.

---

## Claim boundary

- GunnchOS does **not** guarantee HDCP-compliant external display playback today.
- Media Mode shows: *"HDCP may be required for external display"* on DRM services.
- Stripping, bypassing, or spoofing HDCP is **not** supported.

---

## 1. Display topology inventory

| Output | Target SKU | HDCP version required | Status |
|--------|------------|----------------------|--------|
| Internal panel | Reference handheld | Usually N/A for local UI | Not validated |
| HDMI / USB-C DP alt mode | Dock / classroom projector | HDCP 1.4 minimum; 2.2 for 4K HDR tiers | Not validated |
| Wireless display (Miracast/Chromecast) | Optional future | Service-dependent | Not started |
| VR / headset | Out of scope v1 | — | N/A |

---

## 2. Hardware readiness

| Item | Status | Notes |
|------|--------|-------|
| GPU/display driver HDCP capability documented per SKU | Not started | OEM datasheet required |
| Kernel DRM/KMS HDCP hooks identified | Not started | Platform-specific |
| EDID read — display HDCP support bit | Not tested | `collect_reference_hardware_info.py` may extend |
| Hotplug: dock connect during playback | Not tested | — |
| Hotplug: undock during playback | Not tested | Graceful stop expected |

---

## 3. Software stack

| Item | Status | Notes |
|------|--------|-------|
| Browser/CDM negotiates HDCP with compositor | Not started | — |
| OS shows user-visible HDCP status (not false green) | Partial | Warning text in Media Mode |
| Fallback: internal panel only when HDCP fails | Not implemented | — |
| Screenshot / screen capture blocked for DRM content | Not tested | OS policy TBD |

---

## 4. Per-service HDCP expectations

| Service | HDCP for external display | GunnchOS UI |
|---------|---------------------------|-------------|
| YouTube (free) | Usually not required | No HDCP flag |
| Netflix | **Often required** | Disclaimer shown |
| Hulu | **Often required** | Disclaimer shown |
| Disney+ / Max / Prime / others | **Often required** | Future route |
| Local media (non-DRM) | Not required | No HDCP flag |

---

## 5. Test plan (execute on reference hardware)

| Test | Setup | Pass criteria | Evidence |
|------|-------|---------------|----------|
| HDCP-capable monitor | Licensed Netflix/Hulu account, external HDMI | Playback at documented max res OR honest error | `results/streaming/hdcp_pass.md` |
| Non-HDCP monitor / capture card | Same account | Service blocks or downgrades; shell stable | `results/streaming/hdcp_fail.md` |
| Dock hotplug mid-playback | DRM title playing | No crash; user message | Log + capture |
| School projector (typical) | Institution account if available | Document actual behavior | Field report |
| Internal-only fallback | Disable external output | Playback on panel | Capture |

---

## 6. User-facing messaging audit

| Location | Required text present? |
|----------|------------------------|
| Netflix card (Media Mode) | ✓ DRM/CDM + HDCP disclaimer |
| Hulu card (Media Mode) | ✓ DRM/CDM + HDCP disclaimer |
| Settings → Display | Partial (external display placeholder) |
| Beta release notes | Must not claim HDCP validated |

---

## 7. Sign-off (blocked until evidence)

- [ ] Hardware: HDCP-capable path documented per reference SKU
- [ ] QA: Pass and fail monitor tests logged
- [ ] UX: Error states are understandable (not false success)
- [ ] Product: No marketing claim of "works on any projector"

**Owner:** Media platform + hardware validation

---

## Related

- [SERVICE_CERTIFICATION_TRACKER.yaml](SERVICE_CERTIFICATION_TRACKER.yaml)
- [CDM_READINESS_CHECKLIST.md](CDM_READINESS_CHECKLIST.md)
- [STREAMING_COMPATIBILITY_MATRIX.md](STREAMING_COMPATIBILITY_MATRIX.md)
- [../hardware_validation/HARDWARE_CLAIM_BOUNDARY.md](../hardware_validation/HARDWARE_CLAIM_BOUNDARY.md)
