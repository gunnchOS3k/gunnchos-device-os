# Checksums Status

**Status:** `not_started`

---

## Summary

| Item | Status |
|------|--------|
| Checksum generation script | not_started |
| `checksums.sha256` in releases | not_started |
| CI verification step | not_started |
| Manifest hash alignment | planned |

---

## Requirements

Every release artifact must appear in `checksums.sha256`:

```
<sha256>  <relative-path>
```

Manifest must include aggregate hash and be signed (see [SIGNING_REQUIREMENTS.md](SIGNING_REQUIREMENTS.md)).

---

## Planned pipeline

1. Build step emits file list
2. `sha256sum` over each file
3. Attach to release bundle
4. Installer self-verifies before apply
5. CI job verifies checksums on tagged release

---

## Alpha today

- Git commit hashes only — not release checksums
- Demo JSON not checksum-published

---

## RC backlog

Task #4 in [../roadmap/RELEASE_CANDIDATE_BACKLOG.md](../roadmap/RELEASE_CANDIDATE_BACKLOG.md)

---

## Claim boundary

Checksum pipeline is **not yet** operational. No release checksum file exists.
