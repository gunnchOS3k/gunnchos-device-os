# CX2G Linux lab — Chromium shell launch repair on CX2F DRM/Weston

Isolated from Device Lab. Clones CX2F overlay as backing file when present (CX2F immutable); else CX2E.

```bash
python -m gunnchos_device_os.cx2g --prepare-only
python -m gunnchos_device_os.cx2g --full-lifecycle
```

Evidence: `artifacts/complete_experience/cx2g/`

Forbidden: `pkill -f chromium` (self-kills SSH remote shell). Use `stop_owned_shell_runtime()`.
