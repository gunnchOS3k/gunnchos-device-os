# ShellRuntimeTarget v1 (CX2E)

Production shell authority remains **Path B**: `apps/gunnch_shell`.

| Field | Value |
|-------|-------|
| source_sha | git HEAD at build |
| build_hash | sha256 of immutable `dist/` assets |
| arch | aarch64 |
| guest_os | debian-12-bookworm |
| renderer | chromium-app-mode (declared provider) |
| launch_cmd | `chromium --app=file:///opt/cx2e/gunnch_shell/index.html` (+ isolated user-data-dir) |
| content_origin | `file:///opt/cx2e/gunnch_shell/index.html` |
| compositor | weston |
| display_socket | `/run/cx2e-wayland/wayland-0` |
| dbus | `unix:path=/run/cx2e-wayland/bus` |
| a11y_bus | at-spi2 |
| device_profile | `ci_qemu_linux_graphical` |

**Vite `npm run dev` is not production.** Build with `npm run build` only.
