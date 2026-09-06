# Learning OS role mapping (Platform → Device OS)

Documented in `gunnchos_device_os/learning_os/roles.py` and enforced by
`permissions_manager.ROLE_ALLOWLIST`.

| Platform role | Device OS role | Notes |
|---|---|---|
| learner | student | Coursework baseline (read/write/network/sensors/identity) |
| grader | grader | Least privilege for grader workflows — read/network/identity/notifications only; **not** educator |
| instructor | educator | Teaching tools including camera/microphone |
| site_admin | admin | Full Device OS permission set |
| guardian | guardian | Oversight — read/network/notifications/identity |

Grader is intentionally stricter than student (no `files_write`, no `sensors`)
and must not be mapped to educator merely for convenience.
