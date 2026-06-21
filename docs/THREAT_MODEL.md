# Threat Model

**Status:** device OS alpha · research prototype scope  
**Related:** `docs/SECURITY_MODEL.md`, `docs/SECURITY_INVARIANTS.md`

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## Scope

This threat model covers the **gunnchos-device-os alpha package** — Python policy modules, launcher mock, and deploy/Edge-IO contracts — not production hardware secure boot or carrier networks.

---

## Assets

| Asset | Sensitivity |
|-------|-------------|
| Child user profiles | High |
| Research measurement exports | Medium (metadata) |
| Deploy packages | Medium |
| Guardian audit logs (planned) | Medium |
| Fleet enrollment keys (future) | Critical |
| Local project folders (Developer mode) | User-defined |

---

## Threat actors

| Actor | Goal |
|-------|------|
| Malicious classmate | Install unapproved apps, bypass School mode |
| External attacker on LAN | Silent deploy to student device |
| Curious researcher | Accidental private packet capture |
| Compromised deploy bundle | Code execution on target |
| Insider admin | Excessive telemetry collection |

---

## STRIDE summary (alpha mitigations)

| Category | Threat | Alpha mitigation | Gap |
|----------|--------|------------------|-----|
| Spoofing | Fake DS-XL deploy source | Trust prompt placeholder | No cryptographic device identity |
| Tampering | Modified package in transit | signed_bundle_placeholder | No signature verification |
| Repudiation | Deny approving deploy | Audit log placeholder | No persistent log |
| Information disclosure | Telemetry leaks PII | Consent + child defaults off | No network stack |
| Denial of service | Deploy flood | Not addressed | Rate limiting needed |
| Elevation | Child → Developer | guardian_policy + mode_policy | Not kernel-enforced |

---

## Mode-specific threats

| Mode | Primary risk | Control |
|------|--------------|---------|
| School | Surveillance overreach | no_invasive_surveillance |
| Developer | Supply chain in deps | package_dependency_warning flag |
| Research Measurement | Private capture | no_private_packet_capture |
| Admin | Over-privilege | Blocked from School without consent |

---

## Deploy threats

See [LOCAL_DEPLOY_SECURITY_MODEL.md](LOCAL_DEPLOY_SECURITY_MODEL.md).

Key controls: no_silent_deploy, guardian_approval, consent gates.

---

## Edge-IO threats

See [EDGE_IO_PRIVACY_SAFETY.md](EDGE_IO_PRIVACY_SAFETY.md).

Key controls: consent required, no_private_packet_payloads, location off by default.

---

## Out of scope (explicit)

- Hardware tamper resistance
- Baseband / modem exploits
- Steam/account credential phishing (user education only)
- Physical device theft (remote wipe is placeholder in user-focused docs)

---

## Claim boundary

This is a **design-time threat model** for alpha planning — not a formal security assessment or penetration test report.
