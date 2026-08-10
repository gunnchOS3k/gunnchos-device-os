# WP-007 External Security Assessment Packet (E7)

**Status:** Prepared, **not executed**  
**Evidence:** E7 / `EXTERNAL_PENDING`  
**Does not claim:** EXTERNAL pentest PASS, certification, physical fault injection, carrier approval, or `production_ready` security.

---

## 1. Architecture overview

gunnchOS device OS is a research / EVT digital stack:

- Python policy + runtime services (identity, sandbox, OTA sim, AI interface, Ring adapter, continuity, fabric)
- Device Lab virtualization backends (display/storage/network/audio/rings) — not silicon-exact
- DEV-realm signing keys only (in-repo); production keys forbidden
- Golden Journeys G01–G10 digital suite as regression surface

Primary repo: `gunnchos-device-os`  
Related: `gunnchAI3k` (tutor), `gunnchos-hardware-industrial-design` (authenticated ring protocol reference)

## 2. Scope (proposed EXTERNAL engagement)

**In scope**
- Identity/session/revoke and role escalation paths
- Update signing / anti-rollback / recovery
- Package install + sandbox capability boundaries
- AI prompt/tool/computer-use approval paths
- Ring authenticated input + destructive confidence policy
- Continuity/Fabric trust and exfiltration paths
- Device Lab privilege boundary (path/netns/uinput/secrets in manifests)
- Hostile network assumptions (Wi-Fi/DNS/TLS stubs where present)
- Game save/replay integrity digital paths

**Out of scope / excluded destructive actions**
- Physical fault injection / glitching / invasive hardware
- Carrier / SIM / live modem attach
- Production key compromise exercises against live roots (none exist)
- Denial-of-service against third-party infrastructure
- Social engineering of minors / real student PII
- Destructive actions on non-lab production accounts (N/A)

## 3. Test environment

- Digital: clone of `gunnchos-device-os` at frozen tip SHA; Device Lab profiles; Golden Journey fixtures
- Optional: QEMU bootable reference image (DEV realm)
- No production fleet; no live school tenant

## 4. Credentials / accounts plan

| Account | Purpose |
| --- | --- |
| student | Baseline least privilege |
| guest | Isolation / no escalation |
| educator / guardian | Policy elevation (break-glass documented) |
| developer | Toolchain (break-glass) |
| admin | Fleet/MDM sim only |
| Ring DEV token class | `DEV_*` only; prod tokens rejected |

Provide ephemeral lab accounts only. No real WAIKE student data.

## 5. Rules of engagement

1. Work only against designated lab SHA / lab devices.
2. Report S0/S1 within 24h via private advisory channel.
3. Do not publish exploit details until remediation window agreed.
4. No persistence outside lab artifacts directory.
5. Stop and notify if real PII or production credentials discovered (should not exist).

## 6. Data handling

- Lab artifacts under `artifacts/wp007/` and Device Lab instance dirs
- Redact tokens/secrets from reports (hash only)
- Destroy lab accounts at engagement end

## 7. Retest expectations

- All S0/S1 must retest to closed
- S2: fix or accepted risk with owner
- Deliver independent report separate from implementer harness (`gunnchos_device_os/security_red_team`)

## 8. Vendor qualification questions

1. Prior OS / embedded / mobile red-team experience?
2. Ability to assess AI agent tool-boundary abuse?
3. Wireless / BLE input protocol experience (Ring path)?
4. Clearance / youth-safety handling procedures?
5. Deliverable format compatible with evidence ledger (case IDs SEC-*)?
6. Will not claim certification beyond agreed scope?

## 9. Remaining EXTERNAL work checklist

- [ ] Commission qualified EXTERNAL vendor
- [ ] Execute scoped pentest against frozen EVT0 tip (post WP-001 freeze)
- [ ] Physical Ring pairing / RF spoofing (after PHYSICAL freeze lifts)
- [ ] Production signing root ceremony + measured boot on hardware
- [ ] Live connector/MCP/Skills adversarial review
- [ ] Authoritative multiplayer / social anti-cheat review
- [ ] Carrier / MDM remote authority review

Until then: `external_pentest=EXTERNAL_PENDING`.
