# gunnchGuestAgent protocol (`gunnchos.guest_agent.v1`)

Transport: virtio-serial chardev exposed to the host as a unix stream socket
(`server=on`), one JSON object per line in each direction. A file-based
"mailbox" fallback (`*.mailbox` path, request/response file pair) exists for
early bring-up and unit tests only — it is always labeled
`"transport": "host_mailbox_stub"` and never claims to be a live guest.

Every request carries `{"protocol": "gunnchos.guest_agent.v1", "cmd": "<name>", ...}`.
Every response is a JSON object that includes at least `"ok": <bool>`.

## Commands

| Command | Since | Purpose |
|---|---|---|
| `ping` | v1 | Liveness probe. Response includes `"pong": true`. |
| `boot_status` | v1 | Whether guest init has finished. |
| `process_list` | v1 | List of guest processes the agent knows about. |
| `process_start` | v1 | Start a named guest process/service. |
| `process_stop` | v1 | Stop a named guest process/service. |
| `package_ops` | v1 | Guest-side package manager operations (apk). |
| `display_info` | v1 | Enumerate guest DRM/display connectors (used by `GUEST_DUAL_OUTPUT_PASS`). Connector enumeration alone is **not** sufficient for `DSXL_DUAL_COMPOSITOR_UX_PASS` — see `compositor_info` below. |
| `input_inject` | v1 | Inject a key/pointer event from the host into the guest. |
| `input_observe` | v1 | Observe/report the last input event seen by the guest (used by Ring proofs). |
| `logs` | v1 | Tail guest boot/service logs. |
| `metrics` | v1 | Guest resource telemetry (`HOST_OBSERVED` measurement class). |
| `shutdown` / `reboot` | v1 | Guest power control. |
| `framebuffer_capture` | **v1 (Interactive Guest)** | Request a raw framebuffer/DRM capture **from inside the guest compositor** (as opposed to QEMU's host-side `screendump` monitor command, which only proves the virtual scanout memory changed, not that the guest actually rendered a real shell/app surface). Request: `{"cmd": "framebuffer_capture", "path": "<host-visible-or-guest-relative-path>"}`. Response on a real guest: `{"ok": true, "path": ..., "bytes": <int>, "format": "ppm"|"png", "synthetic": false}`. |
| `compositor_info` | **v1 (Interactive Guest)** | Ask whether a Wayland compositor (weston) is actually running, its seat/socket, and output/surface counts. Exists specifically so `DSXL_DUAL_COMPOSITOR_UX_PASS` evidence cannot be satisfied by `display_info` DRM-connector enumeration alone (see `virtualization/dsxl_outputs.py`). Response on a real guest: `{"ok": true, "compositor": "weston", "socket": "wayland-0", "outputs": <int>, "surfaces": <int>}`. |
| `app_launch` | **v1 (Interactive Guest)** | Launch a real in-guest application (browser, editor, game) by name/command. Replaces host-side `http.server` / hybrid-surface proofs with a genuine in-guest process for Ring / FOUR_GAME work. Request: `{"cmd": "app_launch", "app": "chromium", "args": [...]}`. Response on a real guest: `{"ok": true, "pid": <int>, "app": "chromium", "started": true}`. |

## Honesty rules for the three Interactive Guest commands

1. The host mailbox stub (`GuestAgentClient._local_stub`, used only when no
   real virtio-serial guest is connected) **must** answer these three
   commands with `"ok": false` (or an explicit `"available": false"` /
   `"started": false`) and `"stub": true`. It must never fabricate a
   framebuffer file, a fake compositor name, or a fake PID.
2. Callers (`live_visual_proof.py`, `dsxl_outputs.py`,
   `ring_app_mutation.py`, and any future Interactive Guest scenario code)
   must treat a stub response as "not earned" for any `*_PASS` token — never
   as a skip-to-PASS.
3. A real earned response requires an actual virtio-serial-connected guest
   agent running inside a booted Interactive Guest
   (`DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST=true`), which is not yet built
   or booted as of this wave (see
   `os_build/device_lab_interactive_guest/README.md`).
