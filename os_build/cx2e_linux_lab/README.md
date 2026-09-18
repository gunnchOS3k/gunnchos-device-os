# CX2E Linux Graphical Session Lab

Isolated from Device Lab (`os_build/device_lab_interactive_guest/`) and CX2D scaffolding.

- Evidence: `artifacts/complete_experience/cx2e/`
- Entry: `python3 -m gunnchos_device_os.cx2e --full-lifecycle`
- Base image: read-only copy from Device Lab cache into `images/` (never mutate Device Lab)

Truth depends on guest facts (`guest_booted && guest_is_linux && compositor_running && wayland_socket_alive && shell_window_rendered`), not host `platform.system()`.
