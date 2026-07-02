# Phase 4E — Streaming CDM and Certification Readiness

**Branch:** `phase4e-streaming-cdm-certification-readiness`  
**Target blocker:** Streaming certification / CDM integration  
**Last updated:** 2026-07-02

---

## Goal

Create a rigorous streaming compatibility and certification **readiness** package so GunnchOS can track CDM, HDCP, and per-service evidence without falsely claiming Netflix, Hulu, Disney+, or Widevine certification.

---

## Real after this PR

- `streaming_certification/` package with compatibility matrix, CDM checklist, HDCP checklist, and service tracker YAML
- `scripts/validate_streaming_certification_tracker.py` — structural validation + no false certification
- `tests/test_streaming_certification.py` — pytest gate
- `beta_gate/beta_gate_status.yaml` — `streaming_certification: prototype`
- Updated Media Mode and streaming requirements docs with Phase 4E cross-links

---

## Still prototype (honest boundary)

- No Widevine / EME / CDM integration in OS or embedded browser
- No per-service playback validation on reference hardware
- No official partner certification letters
- YouTube/Netflix/Hulu remain **browser route prototypes** (external tab)
- Local media remains a **non-DRM HTML5 path**, separate from streaming CDM

---

## Forbidden claims

- Official Netflix, Hulu, Disney+, Prime, or Widevine certification
- Guaranteed HDCP external display playback
- DRM circumvention or HDCP stripping
- "Streaming works on GunnchOS" without per-service evidence in the tracker

---

## Package layout

```
streaming_certification/
  STREAMING_COMPATIBILITY_MATRIX.md
  CDM_READINESS_CHECKLIST.md
  HDCP_EXTERNAL_DISPLAY_CHECKLIST.md
  SERVICE_CERTIFICATION_TRACKER.yaml
scripts/validate_streaming_certification_tracker.py
tests/test_streaming_certification.py
```

---

## Tracker rules

| `certification_status` | Meaning | `evidence_path` required? |
|------------------------|---------|---------------------------|
| `not_started` | Future route or no work | No |
| `browser_route_prototype` | External tab / UI only | Optional |
| `readiness_prototype` | Checklists and docs only | Yes (readiness doc) |
| `tested_unverified` | Internal smoke, not partner certified | Yes (test log) |
| `certified` | Partner letter or audited certification | **Yes (must exist on disk)** |

The validator and pytest **reject** any service marked `certified` without a resolvable `evidence_path`.

---

## Validation

```bash
python3 scripts/validate_streaming_certification_tracker.py
pytest -q tests/test_streaming_certification.py
make validate-full
```

---

## Next steps (post-4E)

1. Integrate Chromium + Widevine on reference OS image (not this PR).
2. Execute CDM and HDCP test plans; file evidence under `results/streaming/`.
3. Update tracker `certification_status` only with evidence paths.
4. Pursue service partner certification where required — separate legal/OEM track.

---

## Related

- [MEDIA_MODE.md](MEDIA_MODE.md)
- [STREAMING_MEDIA_REQUIREMENTS.md](STREAMING_MEDIA_REQUIREMENTS.md)
- [../streaming_certification/SERVICE_CERTIFICATION_TRACKER.yaml](../streaming_certification/SERVICE_CERTIFICATION_TRACKER.yaml)
- [KNOWN_ISSUES.md](KNOWN_ISSUES.md)
