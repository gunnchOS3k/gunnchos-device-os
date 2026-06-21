# School and Library Requirements

**Status:** mode policies + docs · production shared-device fleet **not deployed**

> Shared devices, classroom/library modes, session privacy. See `docs/SCHOOL_MODE.md`, school mode in `config/modes.yaml`.

---

## Shared device mode

- Multiple user profiles on one device
- Fast profile switch at login
- No cross-profile data leakage
- Admin wipe between classes when configured

---

## Session end behavior

| Setting | Behavior |
|---------|----------|
| Default (library) | Clear ephemeral cache; close apps |
| Classroom | Teacher ends session → cleanup |
| Optional retain | IT policy only; logged |

**No private data retention by default** on shared devices.

---

## Modes

| Mode | Purpose |
|------|---------|
| Classroom | Teacher-led; restricted app set |
| Library | Self-serve catalog; time limits |
| Teacher/mentor | Elevated session controls |
| Offline lesson | Lesson pack without network |

---

## Privacy-safe session end

- Close documents or prompt save to user cloud (if allowed)
- Clear clipboard, downloads temp, browser session
- Security event log entry for session end (no document contents)

---

## App and content policy

- School allowlist only in School/Library modes
- WAIKE lesson packs offline capable
- Deploy from IT bundle or offline export

---

## Repair / support workflow

- IT admin recovery without guardian PIN on org-owned devices
- Asset tag linkage in support ticket template
- See [SUPPORT_AND_REPAIR_REQUIREMENTS.md](SUPPORT_AND_REPAIR_REQUIREMENTS.md)

---

## Alpha evidence

- School mode in mode manager + policy tests
- `classroom_library_shared` deploy target
- School/library test plan in `qa/`

---

## Evidence before RC

- Shared-device session cleanup automated tests
- Library offline lesson scenario in UAT
- Session end privacy checklist signed

---

## Claim boundary

School/library **requirements** are defined. Not production fleet management or certified FERPA compliance without institutional review.
