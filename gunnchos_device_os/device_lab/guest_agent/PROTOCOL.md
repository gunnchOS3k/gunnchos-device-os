# gunnchos.guest_agent.v1

Line-JSON over virtio-serial (`org.gunnchos.guest_agent.0`). Honest: never fabricate a compositor, PID, or save mutation.

## Overlay commands (WP-011R.2)

### `godot_input_overlay`

Install `device_lab_input_overlay.gd` into a LIVE owner Godot `project/` and register the `DeviceLabInputOverlay` autoload.

* Requires `project` and `script_b64`.
* Script must contain `Input.parse_input_event`.
* Rejects `--quit-after` / `get_tree().quit` payloads.
* Does **not** launch ProductionGateHarness. Mutation proof is owner `aa_first_run.cfg` / career persist after the overlay taps `ui_accept` past `BootScene._ready_to_start` and Tutorial Skip.

### `browser_input_overlay`

Install `lab_input_overlay.js` into a LIVE owner web root and patch `index.html`.

* Requires `root` and `script_b64`.
* Rejects `localStorage.setItem` payloads (no fake save).
* Drives real `#btn-new-game` click + `KeyboardEvent` WASD / map travel; owner `saveGame()` persist.
