# Flash / Recovery Tooling (package only)

| Tool | Role | Destructive? | Status |
|---|---|---|---|
| `scripts/bringup_nondestructive.sh` | Collect host facts, validate manifests | No | SHIPPED |
| SWD/USB imagers | Future physical flash | Yes | BLOCKED — freeze |
| Recovery contracts YAML | Safe-mode / recovery boot schema | No | Present in firmware_compat |

Policy: no flash commands invoked by Gate 1 orchestrator.
