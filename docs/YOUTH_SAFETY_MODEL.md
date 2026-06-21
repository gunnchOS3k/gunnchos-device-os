# Youth Safety Model

**Status:** device OS alpha · design intent for youth profiles  
**Modules:** `guardian_controls.py`, `guardian_policy.py`, `mode_policy.py`, `privacy_security_model.py`

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## Principles

1. **No private content inspection** — guardians see policy outcomes, not message bodies or keystrokes
2. **Privacy-safe telemetry** — child profiles default to telemetry off (`privacy_defaults.yaml`)
3. **Age-appropriate defaults** — screen time and content filters scale by band
4. **Guardian approval for escalation** — Developer/Admin/Workshop/Laboratory require approval for younger bands
5. **No invasive surveillance** — School mode sets `no_invasive_surveillance: true`
6. **Emergency unlock path** — `guardian_pin_or_biometric` placeholder (not implemented)

---

## Age band model

| Band | Typical age | Mode approval | App approval | Play window |
|------|-------------|---------------|--------------|-------------|
| pre_k | 3–5 | Yes | Yes | 10:00–11:00 |
| elementary | 6–10 | Yes | Yes | 15:00–17:00 |
| middle_school | 11–13 | Yes | Yes | 15:00–19:00 |
| high_school | 14–18 | No | No | 15:00–21:00 |

Post-secondary bands use light filtering without mandatory app approval.

---

## Content filter tiers

From `guardian_defaults.yaml` → `media_caution`:

| Tier | Blocked/caution apps |
|------|---------------------|
| strict | steam, netflix, hulu, unapproved_chat |
| moderate | netflix, hulu |
| light | (empty) |

---

## Mode alignment

| Mode | Youth safety tier | Notes |
|------|-------------------|-------|
| School | strict | Focus mode, simplified home |
| Guardian | strict | Telemetry none |
| Library | strict | Shared device |
| Play | standard | Time window from guardian config (future enforcement) |
| Developer | standard / gated | Blocked for children without guardian |

---

## Shared device support

`defaults.shared_device_support: true` — Library mode and classroom targets assume no persistent personal accounts.

---

## Product requirements cross-link

See `product/YOUTH_AND_GUARDIAN_REQUIREMENTS.md` for PRD-level requirements (also alpha).

Legacy doc: [GUARDIAN_AND_YOUTH_SAFETY.md](GUARDIAN_AND_YOUTH_SAFETY.md)

---

## Claim boundary

Youth safety in this repo is **policy documentation + mock defaults**. It is not legal compliance certification or production enforcement.
