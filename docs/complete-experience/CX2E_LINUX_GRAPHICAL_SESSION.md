# CX2E — Linux Graphical Session + Journey Proof

Stacked on CX2D (`eng/cx2d-linux-real-user-journey-closure` / Device OS #140).

## Truth gate (guest facts only)

`guest_booted && guest_is_linux && compositor_running && wayland_socket_alive && shell_window_rendered`

Host `platform.system()` alone never grants PASS.

## Lab

- Namespace: `os_build/cx2e_linux_lab/`
- Evidence: `artifacts/complete_experience/cx2e/`
- Entry: `python3 -m gunnchos_device_os.cx2e --full-lifecycle`

## Required session tokens

`CX2E_QEMU_GUEST_BOOT_PASS`, `CX2E_GUEST_LINUX_PROVEN`, `CX2E_WESTON_SESSION_PASS`,
`CX2E_WAYLAND_SOCKET_PASS`, `CX2E_DBUS_SESSION_PASS`, plus portal/shell/input/capture tokens.

`FULL_COMPLETE_EXPERIENCE_COMPLETE=false`
