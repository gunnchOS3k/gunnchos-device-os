# CX2D Linux Lab (isolated)

Distinct from Device Lab Interactive Guest release train (`os_build/device_lab_interactive_guest/`).

## Rules

- Never write Device Lab `artifacts/` or `pipeline/` sealed manifests.
- May **read** Device Lab `cache/debian-12-genericcloud-arm64.qcow2` as a base source.
- All CX2D images/overlays live under `os_build/cx2d_linux_lab/`.
- Evidence only under `artifacts/complete_experience/cx2d/`.

## Target stack

Debian 12 aarch64 · Weston/Wayland · DBus user session · XDG portals · Flatpak · CUPS · Chromium · LibreOffice · AT-SPI (+ Orca) · PipeWire

## Provision

```bash
PYTHONPATH=. python3 os_build/cx2d_linux_lab/scripts/provision_cx2d_linux_lab.py --prepare-only
PYTHONPATH=. python3 -m gunnchos_device_os.cx2d
```

Full guest cloud-init provision is long-running; `--prepare-only` creates overlay + cloud-init and records honest blockers when graphical session is not proven.
