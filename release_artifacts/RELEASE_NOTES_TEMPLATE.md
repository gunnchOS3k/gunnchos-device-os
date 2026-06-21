# Release Notes Template

**Copy for each release** · Replace `{placeholders}`

---

# gunnchOS Release Notes — {version}

**Release date:** {YYYY-MM-DD}  
**Channel:** {stable|beta|dev|school_managed}  
**Gate:** {alpha|beta|release_candidate|ga_release}  
**Supported devices:** {SKU list}

> **Claim check:** Only use GA/RC language if [../release_gates/RELEASE_SIGNOFF_TEMPLATE.md](../release_gates/RELEASE_SIGNOFF_TEMPLATE.md) is signed for this gate.

---

## Summary

{One paragraph: what this release is for and who should install it.}

---

## Highlights

- {Feature or fix}
- {Feature or fix}

---

## Supported hardware

| SKU | Supported | Notes |
|-----|-----------|-------|
| Student 14.5 | {yes/no/partial} | |
| Handheld Hybrid | {yes/no/partial} | |
| DS-XL Coder | {yes/no/partial} | |
| Wearables/Arena | {placeholder/future} | |

---

## Install / upgrade

1. Verify checksums: `{checksums.sha256 link}`
2. Run installer: `{installer filename}`
3. First-run wizard will launch

**Rollback:** Settings → System → Roll back to {previous_version}

---

## Known issues

| ID | Description | Workaround |
|----|-------------|------------|
| | | |

---

## Security

- SBOM: `{sbom link}`
- Security review: `{report link or N/A for alpha}`

---

## Accessibility

- Validation report: `{link or "not yet — validation track only"}`

---

## Operator notes (IT / admin)

- {Managed update channel notes}
- {School/library session cleanup changes}

---

## Explicit non-claims

This release does **not** claim (unless evidence linked above):

- Finished shipping OS on unreleased hardware
- Production MDM deployment
- Accessibility certification
- Official Steam/media partner certification

---

## Artifact manifest

| Artifact | SHA-256 |
|----------|---------|
| | |

---

## Support

- Troubleshooting: {link}
- Report issues: {link}
