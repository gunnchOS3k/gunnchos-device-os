# Security and Privacy Requirements

**Status:** alpha models + partial threat model · **security review not complete**

> Baseline for shippable gunnchOS. Based on secure software development principles. See `docs/THREAT_MODEL.md`, `docs/PRIVACY_SECURITY_MODEL.md`. This document does not claim secure boot complete on all devices or production MDM deployed without evidence.

---

## Required security artifacts

| Artifact | Requirement | Current status |
|----------|-------------|----------------|
| Threat model | Maintained per release; STRIDE or equivalent | Partial in `docs/THREAT_MODEL.md` |
| Security event log | Local tamper-evident audit | `security_event_log.py` + tests |
| Vulnerability disclosure policy | Published contact + SLA | **planned** |
| Dependency review | Pre-release scan | CI partial |
| SBOM | Per release | requirement only |
| Secrets scan | Pre-commit / CI | **planned** |
| Release signing plan | Manifest + bundle | [../release_artifacts/SIGNING_REQUIREMENTS.md](../release_artifacts/SIGNING_REQUIREMENTS.md) |

---

## Security principles

### Least privilege

- Apps run with minimum permissions per mode policy
- Guardian/school policies restrict elevated actions
- Developer mode requires explicit unlock where policy demands

### Update and rollback integrity

- Signed manifests only; reject unsigned bundles
- Rollback bundles equally signed (see update requirements)

### Data minimization

- Collect only consented telemetry fields (`consent_policy.py`)
- Child/youth defaults: telemetry off unless guardian opt-in
- Local-only mode: no cloud egress for marked workflows

### Consent states

| State | Behavior |
|-------|----------|
| Unknown | Minimal functionality; prompt on first use |
| Denied | No optional telemetry; local features only |
| Guardian-managed | Child profile inherits guardian choice |
| School-managed | IT policy overrides where legally permitted |

### Export / delete path

- User-initiated export of profile metadata (design)
- Delete request queues local wipe — **full pipeline not production-proven**

### No hidden telemetry

- All channels documented in telemetry consent UI
- Security event log separate from product telemetry

### No private content inspection by default

- No cloud scanning of documents, chat, or media without explicit consent and policy

---

## Privacy modules (alpha evidence)

| Module | Evidence |
|--------|----------|
| `privacy_security_model.py` | pytest |
| `consent_policy.py` | pytest |
| `security_event_log.py` | pytest |
| `config/privacy_defaults.yaml` | child telemetry off default |

---

## Youth and child defaults

- Telemetry off by default for child profiles
- Guardian approval for app install and mode transitions (policy stubs)
- COPPA/GDPR alignment is a **legal review** — not claimed by OS repo alone

---

## Evidence before RC

- Security review checklist complete
- Secrets scan in CI
- SBOM generated for RC bundle
- Threat model reviewed for update/signing paths

---

## Evidence before GA

- External security review or red-team summary (if required by policy)
- 90-day vulnerability response drill documented

---

## Claim boundary

Privacy/security **baseline** is defined and partially implemented in alpha. The repo does **not** claim complete secure boot on all devices, production MDM deployed, or that security review is complete.
