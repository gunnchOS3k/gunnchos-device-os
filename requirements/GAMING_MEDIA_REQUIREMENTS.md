# Gaming and Media Requirements

**Status:** Steam/media mocks · **no official Steam/media certification**

> Play mode gaming and media consumption. See `steam_integration.py`, `media_apps.py`.

---

## Steam launch path

| Requirement | Description |
|-------------|-------------|
| Launch from Play Mode | Single-tap Steam entry when policy allows |
| Account boundary | User's Steam account; gunnchOS does not store credentials |
| Offline boundary | Steam offline mode per Valve policy — no DRM bypass |
| Performance profile | Play mode governor reduces background tasks |
| Controller mapping | Handheld Hybrid primary; Student 14.5 optional controller |

---

## Play time policy

- Guardian schedules and daily limits (policy stubs)
- School mode may block Play entirely
- Clear notification before limit reached

---

## Media / browser path

- Media apps route from Media mode
- Browser with guardian/school filter hooks (placeholder)
- Captions preference honored
- External display/dock: mirror or extend per dock manager design

---

## School / guardian restrictions

| Policy | Effect |
|--------|--------|
| School hours | Block Play and non-educational media |
| Age band | Restrict M-rated content hooks |
| Guardian deny list | Block specific apps |

---

## DRM boundary

- **No DRM bypass** — ever
- Document partner DRM requirements; do not implement circumvention
- Offline game boundary: only per store/offline license rules

---

## Alpha evidence

| Component | Status |
|-----------|--------|
| `steam_integration.py` | mock + demo JSON |
| `media_apps.py` | mock |
| `performance_governor.py` | prototype |

---

## Evidence before RC

- Steam/media route dry-run tests (mock launch log)
- Guardian block tests for Play mode
- Dock external display smoke (hardware when available)

---

## Forbidden claims

- Official Steam certification
- Official media app certification
- Guaranteed game compatibility on all hardware

---

## Claim boundary

Gaming and media **requirements** are defined. Routes are mocks — not partner-certified integrations.
