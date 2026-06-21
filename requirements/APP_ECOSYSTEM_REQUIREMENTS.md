# App Ecosystem Requirements

**Status:** policy stubs + launcher mock · production app store **not built**

> Requirements for app registry, packs, workspaces, and trust on gunnchOS.

---

## App registry

- Central registry schema: id, version, trust tier, mode allowlist, offline flag
- Source: signed bundles, school library catalog, guardian-approved list
- Metadata schema documented for RC (see deploy package format for deployable apps)

---

## App packs

| Pack type | Examples | Policy |
|-----------|----------|--------|
| School | Lesson tools, WAIKE cards | School mode allowlist |
| Play | Games, Steam shortcut | Guardian time + age band |
| Developer | VS Code, terminal, Git | Developer unlock |
| Creator | Writer, art, music | Studio modes |
| Offline | Bundled lesson packs | No network required after install |

---

## Workspaces

- Workspace = layout + app pack + accessibility preset
- User can save custom workspace from preset
- Import/export as signed profile fragment

---

## Install / launch / uninstall policy

| Action | Guardian | School | Admin |
|--------|----------|--------|-------|
| Install from network | Approval required (child) | IT allowlist | Unrestricted |
| Launch | Mode + time policy | Session scoped | Audit logged |
| Uninstall | Approval for child | Wipe on session end (shared) | Full remove |

---

## Offline apps

- Must declare offline capability in metadata
- Updates via offline bundle only when in offline mode
- Failure fallback: cached last version or safe error

---

## App failure fallback

- Crash → offer restart, safe mode, report (consented)
- No silent relaunch loop
- School shared device: kill app + clear session cache

---

## App trust model

| Tier | Meaning |
|------|---------|
| System | Shipped with gunnchOS |
| Signed partner | Signed by gunnchOS partner key |
| School | IT-side loaded |
| User | Guardian-approved sideload |
| Blocked | Deny list |

---

## App metadata schema (minimum fields)

```yaml
app_id: string
version: semver
trust_tier: system | signed_partner | school | user | blocked
modes_allowed: [school, play, ...]
offline_capable: boolean
age_min: integer | null
guardian_approval_required: boolean
```

---

## Alpha evidence

- Deploy contract package types in `config/deploy_targets.yaml`
- Launcher mock app pack routes
- `policy_engine.py` tests (app policies testable)

---

## Evidence before RC

- App pack install/launch automated tests
- Trust tier enforcement tests
- Uninstall cleanup on shared device

---

## Claim boundary

App ecosystem **requirements** are defined. No claim of production app store or official third-party certification.
