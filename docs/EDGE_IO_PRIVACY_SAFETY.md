# Edge-IO Privacy & Safety

**Status:** device OS alpha · consent-first measurement design  
**Modules:** `edge_io_contract.py`, `mode_policy.py`, `privacy_security_model.py`

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## Core rules

1. **Consent before start** — `start_field_session(..., consent=False)` blocks with safe message
2. **Research operator profile** — `requires_research_operator: true` in contract
3. **No private packet payloads** — aggregate metadata only
4. **No silent background** — `no_silent_background: true`
5. **User can stop** — `stop_session()` always available in API
6. **Local-only default** — data stays on device unless explicit export
7. **Location off by default** — metric flag `location_optional_off_by_default`

---

## Consent denied behavior

From `failure_modes.consent_denied`:

| Field | Value |
|-------|-------|
| user_message | "Measurement stopped. No data was collected." |
| safe_fallback | local_only |
| next_action | return_to_launcher |

---

## Mode policy alignment

Research Measurement mode:

- `no_private_packet_capture: true`
- `consent_prompts: true`
- `local_only_logging: true`

`research_mode_policy()` blocks: private_packet_capture, message_content, keystroke_logging.

---

## Child and school profiles

Field sessions should run under **research operator** adult profiles — not elementary School mode without guardian + research consent.

WAIKE tutor card `lab_field_measurement` includes safety note: "No private packet capture. Location off by default."

---

## Export safety

Exports include `no_private_payloads: True` on success path.

Users choose csv/json — no binary PCAP export in contract.

---

## Fleet / launcher mock

Fleet view shows synthetic telemetry — labeled **not** Edge-IO field data.

---

## Cross-repo

Full privacy model in [edge-io-measurement-node](https://github.com/gunnchOS3k/edge-io-measurement-node) — this repo defines **device OS integration contract only**.

---

## Claim boundary

Privacy rules are **design requirements** for alpha — not proof of IRB approval or regulatory compliance.

See [EDGE_IO_FAILURE_MODES.md](EDGE_IO_FAILURE_MODES.md).
