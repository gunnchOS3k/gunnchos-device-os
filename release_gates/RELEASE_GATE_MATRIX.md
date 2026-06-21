# Release Gate Matrix

**Last updated:** 2026-06-21 · honest statuses · **GA release not met**

| Gate | Required evidence | Current evidence | Status | Blocking? | Owner |
|------|-------------------|------------------|--------|-----------|-------|
| **Alpha** | Python modules, YAML configs, launcher mock, demo JSON, pytest green, architecture docs | `gunnchos_device_os/*`, configs, `apps/launcher_mock/`, demo scripts, CI pytest | **evidence_exists** | No (baseline) | OS team |
| **User-focused alpha** | 11 persona scenarios in demo output | `results/user_focused_os_demo_output.json` | **validated** | No | UX |
| **Issue backlog OS alpha** | Device classes, modes, deploy, guardian, privacy, Edge-IO, WAIKE modules + tests | Modules per `docs/ISSUE_BACKLOG_AUDIT.md` | **evidence_exists** | No | OS team |
| **Shippable requirements** | Requirements, gates, artifacts, QA, roadmap docs | This documentation package | **evidence_exists** | No | Release |
| **Beta** | Internal installer prototype, version manifest draft, launcher e2e smoke | Not built | **not_started** | Yes (for beta claim) | Release eng |
| **Release candidate** | Signed bundle, checksums, SBOM, recovery, RC test reports | Not produced | **not_started** | Yes (for RC claim) | Release eng |
| **Installable image** | Install/uninstall/upgrade on reference hardware | Documented only | **not_started** | Yes (for RC+) | Release eng |
| **Update / rollback** | Signed manifest pipeline + rollback drill log | `updater.py`/`rollback.py` mocks | **in_progress** | Yes (for RC+) | Release eng |
| **Hardware compatibility** | Per-SKU physical test report | Profile manifests, compatibility engine, simulated boot readiness, demo JSON (`hardware_compat/`) | **evidence_exists** (simulated only) | Yes (for hardware-compatible release claim) | HW + OS |
| **Accessibility conformance** | Validation report on hardware | Contract docs + mock labels | **not_started** | Yes (for GA a11y claims) | UX + QA |
| **Security review** | Completed checklist + threat model sign-off | Partial threat model | **in_progress** | Yes (for RC+) | Security |
| **GA release** | GA gate artifacts + UAT + support runbooks | **Not met** | **not_started** | Yes (for GA claim) | Release |
| **Field pilot** | Pilot enrollment + field support playbook | Not started | **not_started** | Yes (for pilot claim) | Programs |
| **Production release** | Fleet update channel, production signing, SLA | Not started | **not_started** | Yes (for production claim) | Ops |

---

## Summary (honest)

| Statement | True today? |
|-----------|-------------|
| User-focused alpha exists | **Yes** |
| Issue backlog OS alpha exists | **Yes** |
| Shippable requirements exist | **Yes** |
| Installable image proven | **No** |
| Update/rollback production-proven | **No** |
| Hardware compatibility physically proven | **No** (simulated/profile-based only) |
| Accessibility conformance certified | **No** |
| Security review complete | **No** |
| GA release met | **No** |

---

## Related

- [RELEASE_BLOCKERS.md](RELEASE_BLOCKERS.md)
- [../requirements/SHIPPABLE_OS_REQUIREMENTS.md](../requirements/SHIPPABLE_OS_REQUIREMENTS.md)
