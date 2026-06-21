# Release Evidence Matrix

**Purpose:** Map each gate to concrete evidence artifacts and storage location.

| Gate | Evidence type | Artifact | Location / command | Status |
|------|---------------|----------|-------------------|--------|
| Alpha | Automated | pytest log | CI artifact | evidence_exists |
| Alpha | Demo JSON | user_focused_os_demo_output.json | `results/` | validated |
| Alpha | Demo JSON | mode/deploy/privacy demos | `results/` | evidence_exists |
| Alpha | Docs | Architecture + issue closure | `docs/` | evidence_exists |
| Beta | Build | Installer prototype | TBD release bucket | not_started |
| Beta | Test | Launcher e2e report | `qa/reports/` TBD | not_started |
| RC | Build | Signed bundle + manifest | TBD | not_started |
| RC | Build | Checksums file | TBD | not_started |
| RC | Compliance | SBOM | TBD | not_started |
| RC | Compliance | Security review PDF | TBD | in_progress |
| RC | QA | UAT report | `qa/reports/` TBD | not_started |
| RC | QA | Accessibility report | `qa/reports/` TBD | not_started |
| RC | HW | Compatibility report | TBD | not_started |
| GA | Sign-off | GA release sign-off | [RELEASE_SIGNOFF_TEMPLATE.md](RELEASE_SIGNOFF_TEMPLATE.md) | not_started |
| GA | Support | Runbooks | `docs/` partial | in_progress |
| Field pilot | Ops | Pilot completion report | TBD | not_started |
| Production | Ops | Rollback drill log | TBD | not_started |

---

## Evidence retention

- CI logs: 90 days minimum
- Release artifacts: indefinite per semver tag
- QA signed reports: life of release + one major version

---

## Verification commands

```bash
python scripts/validate_shippable_requirements.py
python scripts/validate_release_gates.py
python scripts/validate_release_artifacts.py
python scripts/validate_qa_package.py
PYTHONPATH=.:src pytest -q tests/
```

---

## Claim boundary

Empty cells mean **no claim** for that gate. Do not mark evidence `validated` without stored artifact hash in sign-off.
