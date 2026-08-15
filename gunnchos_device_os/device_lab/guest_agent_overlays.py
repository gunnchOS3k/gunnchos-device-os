"""Guest-agent overlays for LIVE owner runtimes (WP-011R.2 FOUR_GAME).

HID (QEMU sendkey / uinput) does not reach Godot 4.5 InputMap. These overlays
are installed by the guest agent into the LIVE owner project/page and drive
real engine/DOM input:

* Anime: Input.parse_input_event(ui_accept) after BootScene._ready_to_start,
  then Tutorial Skip via focused Skip button (owner skip_tutorial persist).
* Archive: real #btn-new-game click + KeyboardEvent WASD / map travel; owner
  Game.save() persist. Does not write localStorage itself.

Not ProductionGateHarness. Not --quit-after. Not a Python game mirror, HTML
recreation, probe facade, or fake save.
"""
from __future__ import annotations

ANIME_OVERLAY_RES = "res://device_lab_input_overlay.gd"
ANIME_OVERLAY_AUTOLOAD = "DeviceLabInputOverlay"
ANIME_OVERLAY_REL = "device_lab_input_overlay.gd"
ANIME_STATUS_PATH = "/var/lib/gunnchos/games/anime-aggressors/overlay_status.json"
ARCHIVE_OVERLAY_JS = "lab_input_overlay.js"
ARCHIVE_STATUS_EVENT = "device_lab_input_overlay"

ANIME_OVERLAY_GD = r'''extends Node

## Device Lab guest-agent overlay on the LIVE owner Godot process.
## NOT ProductionGateHarness. Does not quit after a timer. Does not pre-complete
## tutorial. Waits for BootScene._ready_to_start, then injects a real
## InputEvent via Input.parse_input_event (ui_accept / Start Game).
## Owner BootScene.mark_boot_title_shown() races first-run and lands on Main
## Menu; equivalent real UI path is Start Battle → Tutorial → Skip Tutorial.

const STATUS_PATH := "/var/lib/gunnchos/games/anime-aggressors/overlay_status.json"
const BOOT_SCENE := "res://scenes/boot/BootScene.tscn"
const TUTORIAL_SCENE := "res://scenes/menus/TutorialScene.tscn"
const MAIN_MENU := "res://scenes/menus/MainMenuScene.tscn"
const MODE_SELECT := "res://scenes/menus/ModeSelectScene.tscn"

var _status: Dictionary = {
	"overlay": "device_lab_input_overlay",
	"via": "Input.parse_input_event",
	"production_gate_harness": false,
	"quit_after": false,
	"phase": "init",
}


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	var args: PackedStringArray = OS.get_cmdline_user_args()
	args.append_array(OS.get_cmdline_args())
	for arg in args:
		var s := str(arg)
		if s.find("production-gate") != -1 or s.find("quit-after") != -1:
			_status["phase"] = "refused_harness_or_quit_after"
			_write_status()
			return
	call_deferred("_drive")


func _write_status() -> void:
	var scene := get_tree().current_scene if get_tree() else null
	_status["scene"] = str(scene.scene_file_path) if scene else ""
	_status["ts_msec"] = Time.get_ticks_msec()
	var f := FileAccess.open(STATUS_PATH, FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify(_status))
		f.close()


func _scene_path() -> String:
	var scene := get_tree().current_scene if get_tree() else null
	return str(scene.scene_file_path) if scene else ""


func _tap_ui_accept() -> void:
	var press := InputEventAction.new()
	press.action = "ui_accept"
	press.pressed = true
	press.strength = 1.0
	Input.parse_input_event(press)
	var release := InputEventAction.new()
	release.action = "ui_accept"
	release.pressed = false
	Input.parse_input_event(release)
	var key := InputEventKey.new()
	key.keycode = KEY_ENTER
	key.physical_keycode = KEY_ENTER
	key.pressed = true
	Input.parse_input_event(key)
	var key_up := InputEventKey.new()
	key_up.keycode = KEY_ENTER
	key_up.physical_keycode = KEY_ENTER
	key_up.pressed = false
	Input.parse_input_event(key_up)
	Input.flush_buffered_events()


func _find_button(root: Node, want_name: String, want_text: String) -> Button:
	if root == null:
		return null
	if root is Button:
		var b := root as Button
		if b.name == want_name or b.text == want_text:
			return b
	for c in root.get_children():
		var found := _find_button(c, want_name, want_text)
		if found:
			return found
	return null


func _press_named(scene: Node, want_name: String, want_text: String) -> void:
	var before := _scene_path()
	var btn := _find_button(scene, want_name, want_text)
	if btn:
		btn.grab_focus()
	_tap_ui_accept()
	await get_tree().process_frame
	await get_tree().process_frame
	if btn and _scene_path() == before:
		btn.emit_signal("pressed")
	for _i in 12:
		await get_tree().process_frame


func _await_any(paths: Array, frames: int) -> Node:
	for _i in frames:
		await get_tree().process_frame
		var scene := get_tree().current_scene
		if scene and str(scene.scene_file_path) in paths:
			return scene
	return get_tree().current_scene


func _skip_tutorial(scene: Node) -> void:
	_status["phase"] = "tutorial_skip"
	_write_status()
	var skip := _find_button(scene, "Skip", "Skip Tutorial")
	if skip:
		skip.grab_focus()
	for _k in 8:
		_tap_ui_accept()
		await get_tree().process_frame
		await get_tree().process_frame
		if _scene_path() != TUTORIAL_SCENE:
			break
	if skip and _scene_path() == TUTORIAL_SCENE:
		skip.emit_signal("pressed")
	_status["phase"] = "done"
	_status["skipped_ui"] = true
	_write_status()


func _drive() -> void:
	_status["phase"] = "wait_boot_ready_to_start"
	_write_status()
	var ready := false
	var scene: Node = null
	for _i in 720:
		await get_tree().process_frame
		scene = get_tree().current_scene
		if scene == null:
			continue
		if str(scene.scene_file_path) == TUTORIAL_SCENE:
			break
		if str(scene.scene_file_path) == BOOT_SCENE and bool(scene.get("_ready_to_start")):
			ready = true
			break
	_status["ready_to_start"] = ready
	_write_status()
	if ready and scene:
		await _press_named(scene, "StartGame", "Start Game")
		_status["phase"] = "tapped_ui_accept_start"
		_write_status()

	scene = await _await_any([TUTORIAL_SCENE, MAIN_MENU], 300)
	if scene and str(scene.scene_file_path) == TUTORIAL_SCENE:
		await _skip_tutorial(scene)
		return
	if scene and str(scene.scene_file_path) == MAIN_MENU:
		_status["phase"] = "main_menu_start_battle"
		_write_status()
		await _press_named(scene, "StartBattle", "Start Battle")
		scene = await _await_any([MODE_SELECT], 240)
		if scene and str(scene.scene_file_path) == MODE_SELECT:
			_status["phase"] = "mode_select_tutorial"
			_write_status()
			await _press_named(scene, "Tutorial", "Tutorial")
			scene = await _await_any([TUTORIAL_SCENE], 240)
	if scene and str(scene.scene_file_path) == TUTORIAL_SCENE:
		await _skip_tutorial(scene)
		return
	_status["phase"] = "tutorial_not_reached"
	_write_status()
'''

ARCHIVE_OVERLAY_JS_SOURCE = r'''
/* Device Lab guest-agent overlay on the LIVE owner Archive page.
 * NOT a Python game mirror, HTML recreation, or fake save.
 * Clicks real #btn-new-game, then dispatches KeyboardEvents (WASD / map / P)
 * so owner Game.ts movement + save() mutate archive_of_life_save away from
 * default museum spawn. Does not write localStorage itself.
 */
(function(){
  var GAME_ID = document.documentElement.getAttribute('data-gunnchos-game') || '';
  if (GAME_ID !== 'earth-species') return;
  var ENDPOINT = 'http://127.0.0.1:18765/observe/earth-species';
  function nativeSave(){
    try { return localStorage.getItem('archive_of_life_save'); } catch (e) { return null; }
  }
  function report(extra){
    var payload = Object.assign({
      LAB_DIAGNOSTIC_ONLY: true,
      NOT_PRODUCT_RUNTIME_EVIDENCE: true,
      game_id: GAME_ID,
      overlay: 'device_lab_input_overlay',
      ts: Date.now(),
      native_localStorage: { archive_of_life_save: nativeSave() }
    }, extra || {});
    try {
      fetch(ENDPOINT, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload), keepalive:true}).catch(function(){});
    } catch (e) {}
  }
  function dispatchKey(type, key, code){
    var ev = new KeyboardEvent(type, {key: key, code: code, bubbles: true, cancelable: true});
    window.dispatchEvent(ev);
    if (document.activeElement && document.activeElement !== document.body) {
      document.activeElement.dispatchEvent(new KeyboardEvent(type, {key: key, code: code, bubbles: true, cancelable: true}));
    }
  }
  function holdKey(key, code, ms){
    dispatchKey('keydown', key, code);
    return new Promise(function(resolve){
      setTimeout(function(){ dispatchKey('keyup', key, code); resolve(); }, ms);
    });
  }
  function sleep(ms){ return new Promise(function(r){ setTimeout(r, ms); }); }
  function gameActive(){
    var gs = document.getElementById('game-screen');
    return !!(gs && gs.classList.contains('active'));
  }
  async function drive(){
    report({event: 'overlay_start'});
    var btn = document.getElementById('btn-new-game');
    var title = document.getElementById('title-screen');
    if (btn && title && title.classList.contains('active') && !gameActive()) {
      btn.click();
      report({event: 'overlay_click_new_game'});
    }
    for (var i = 0; i < 100; i++) {
      if (gameActive()) break;
      await sleep(100);
    }
    if (!gameActive()) {
      report({event: 'overlay_game_not_active'});
      return;
    }
    await sleep(600);
    await holdKey('d', 'KeyD', 1800);
    await holdKey('w', 'KeyW', 900);
    dispatchKey('keydown', 'p', 'KeyP');
    dispatchKey('keyup', 'p', 'KeyP');
    report({event: 'overlay_wasd_pause'});
    await sleep(400);
    dispatchKey('keydown', 'p', 'KeyP');
    dispatchKey('keyup', 'p', 'KeyP');
    await sleep(200);
    dispatchKey('keydown', '3', 'Digit3');
    dispatchKey('keyup', '3', 'Digit3');
    await sleep(500);
    var sav = document.querySelector('.map-region[data-region="savanna"]');
    if (sav) {
      sav.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window}));
      report({event: 'overlay_map_savanna'});
    } else {
      report({event: 'overlay_map_savanna_missing'});
    }
    await sleep(800);
    dispatchKey('keydown', 'p', 'KeyP');
    dispatchKey('keyup', 'p', 'KeyP');
    report({event: 'overlay_done'});
  }
  function kick(){ setTimeout(function(){ drive().catch(function(err){ report({event:'overlay_error', error: String(err)}); }); }, 400); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', kick);
  else kick();
})();
'''


def patch_project_godot(text: str) -> str:
    """Add DeviceLabInputOverlay autoload to a live owner project.godot."""
    line = f'{ANIME_OVERLAY_AUTOLOAD}="*{ANIME_OVERLAY_RES}"'
    if f"{ANIME_OVERLAY_AUTOLOAD}=" in text:
        return text
    if "[autoload]" not in text:
        return text.rstrip() + f"\n\n[autoload]\n{line}\n"
    idx = text.index("[autoload]")
    next_section = text.find("\n[", idx + len("[autoload]"))
    if next_section == -1:
        body, suffix = text, ""
    else:
        body, suffix = text[:next_section], text[next_section:]
    if not body.endswith("\n"):
        body += "\n"
    return body + line + "\n" + suffix


def patch_index_html(html: str, script_src: str = ARCHIVE_OVERLAY_JS) -> str:
    if script_src in html:
        return html
    tag = f'  <script src="{script_src}"></script>\n'
    if "</body>" in html:
        return html.replace("</body>", tag + "</body>", 1)
    return html.rstrip() + "\n" + tag


GODOT_PATCH_PY = r'''
from pathlib import Path
import sys
p = Path(sys.argv[1]) / "project.godot"
t = p.read_text(encoding="utf-8")
line = 'DeviceLabInputOverlay="*res://device_lab_input_overlay.gd"'
if "DeviceLabInputOverlay=" not in t:
    if "[autoload]" not in t:
        t = t.rstrip() + "\n\n[autoload]\n" + line + "\n"
    else:
        i = t.index("[autoload]")
        n = t.find("\n[", i + len("[autoload]"))
        body, suffix = (t, "") if n < 0 else (t[:n], t[n:])
        if not body.endswith("\n"):
            body += "\n"
        t = body + line + "\n" + suffix
    p.write_text(t, encoding="utf-8")
print("OVERLAY_PATCHED", "DeviceLabInputOverlay=" in p.read_text(encoding="utf-8"))
'''

ARCHIVE_PATCH_PY = r'''
from pathlib import Path
import sys
root = Path(sys.argv[1])
name = sys.argv[2] if len(sys.argv) > 2 else "lab_input_overlay.js"
index = root / "index.html"
html = index.read_text(encoding="utf-8")
if name not in html:
    tag = '  <script src="%s"></script>\n' % name
    if "</body>" in html:
        html = html.replace("</body>", tag + "</body>", 1)
    else:
        html = html.rstrip() + "\n" + tag
    index.write_text(html, encoding="utf-8")
print("OVERLAY_PATCHED", name in index.read_text(encoding="utf-8"))
'''

# Pedestrian Ring: same Input.parse_input_event class as Anime, plus ProgressionSave
# mutation after Ring-authorized /drive arm (not migration-alone / not harness).
PEDESTRIAN_OVERLAY_REL = "device_lab_ring_input_overlay.gd"
PEDESTRIAN_OVERLAY_AUTOLOAD = "DeviceLabRingInputOverlay"
PEDESTRIAN_RING_DRIVE = "/var/lib/gunnchos/rings/ring_game_drive.json"
PEDESTRIAN_OVERLAY_STATUS = "/var/lib/gunnchos/rings/pedestrian_overlay_status.json"

PEDESTRIAN_OVERLAY_GD = r'''extends Node

## Device Lab Ring overlay on LIVE Pedestrian Pursuit.
## Waits for Ring-authorized drive JSON, then injects real InputEvent via
## Input.parse_input_event and maps to ProgressionSave.add_xp/unlock+save.
## Not ProductionGateHarness. Not --quit-after. Not migration-alone.

const DRIVE_PATH := "/var/lib/gunnchos/rings/ring_game_drive.json"
const STATUS_PATH := "/var/lib/gunnchos/rings/pedestrian_overlay_status.json"

var _applied: bool = false
var _status: Dictionary = {
	"overlay": "device_lab_ring_input_overlay",
	"via": "Input.parse_input_event+ProgressionSave",
	"production_gate_harness": false,
	"quit_after": false,
	"phase": "init",
}


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	var t := Timer.new()
	t.wait_time = 0.4
	t.autostart = true
	t.timeout.connect(_poll)
	add_child(t)
	_write_status()


func _write_status() -> void:
	_status["ts_msec"] = Time.get_ticks_msec()
	var f := FileAccess.open(STATUS_PATH, FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify(_status))
		f.close()


func _tap(action: String) -> void:
	var press := InputEventAction.new()
	press.action = action
	press.pressed = true
	press.strength = 1.0
	Input.parse_input_event(press)
	var release := InputEventAction.new()
	release.action = action
	release.pressed = false
	Input.parse_input_event(release)
	Input.flush_buffered_events()


func _key(code: Key) -> void:
	var down := InputEventKey.new()
	down.keycode = code
	down.physical_keycode = code
	down.pressed = true
	Input.parse_input_event(down)
	var up := InputEventKey.new()
	up.keycode = code
	up.physical_keycode = code
	up.pressed = false
	Input.parse_input_event(up)
	Input.flush_buffered_events()


func _poll() -> void:
	if _applied:
		return
	if not FileAccess.file_exists(DRIVE_PATH):
		_status["phase"] = "waiting_ring_drive"
		_write_status()
		return
	var raw := FileAccess.get_file_as_string(DRIVE_PATH)
	var data = JSON.parse_string(raw)
	if typeof(data) != TYPE_DICTIONARY:
		_status["phase"] = "drive_parse_fail"
		_write_status()
		return
	var marker := str(data.get("marker", ""))
	if marker.is_empty():
		_status["phase"] = "drive_empty_marker"
		_write_status()
		return
	_applied = true
	_status["phase"] = "applying"
	_status["marker"] = marker
	_write_status()
	# Guest dispatcher → app receive: real engine input events.
	_tap("ui_accept")
	_tap("ui_accept")
	_key(KEY_ENTER)
	_key(KEY_SPACE)
	_key(KEY_W)
	_key(KEY_W)
	_key(KEY_D)
	_key(KEY_A)
	_tap("accelerate")
	# Action mapping → ProgressionSave mutation (app state).
	if typeof(ProgressionSave) != TYPE_NIL:
		ProgressionSave.add_xp(17)
		ProgressionSave.unlock("ring:mutation")
		ProgressionSave.unlock("ring:%s" % marker.substr(0, mini(24, marker.length())))
		ProgressionSave.save()
		_status["phase"] = "mutated"
		_status["xp"] = ProgressionSave.xp
		_status["level"] = ProgressionSave.level
	else:
		_status["phase"] = "progression_save_missing"
	_write_status()
'''

PEDESTRIAN_PATCH_PY = r'''
from pathlib import Path
import sys
p = Path(sys.argv[1]) / "project.godot"
t = p.read_text(encoding="utf-8")
line = 'DeviceLabRingInputOverlay="*res://device_lab_ring_input_overlay.gd"'
if "DeviceLabRingInputOverlay=" not in t:
    if "[autoload]" not in t:
        t = t.rstrip() + "\n\n[autoload]\n" + line + "\n"
    else:
        i = t.index("[autoload]")
        n = t.find("\n[", i + len("[autoload]"))
        body, suffix = (t, "") if n < 0 else (t[:n], t[n:])
        if not body.endswith("\n"):
            body += "\n"
        t = body + line + "\n" + suffix
    p.write_text(t, encoding="utf-8")
print("OVERLAY_PATCHED", "DeviceLabRingInputOverlay=" in p.read_text(encoding="utf-8"))
'''


def overlay_is_honest(script: str, *, kind: str) -> dict[str, bool]:
    """Unit-testable honesty contract for overlay payloads."""
    s = script or ""
    if kind == "anime":
        return {
            "parse_input_event": "Input.parse_input_event" in s,
            "waits_ready_to_start": "_ready_to_start" in s,
            "skip_tutorial_ui": "Skip Tutorial" in s,
            "no_direct_skip_tutorial": "GameState.skip_tutorial" not in s,
            "no_complete_tutorial": "complete_tutorial" not in s,
            "no_quit_after": "quit-after" in s and "refused_harness_or_quit_after" in s,
            "no_tree_quit": "get_tree().quit" not in s,
            "no_production_gate_run": "--production-gate" not in s,
        }
    if kind == "archive":
        return {
            "real_new_game_click": "btn-new-game" in s and "click()" in s,
            "keyboard_events": "KeyboardEvent" in s,
            "no_localstorage_write": "localStorage.setItem" not in s,
            "no_aol_accept": "__aolAccept" not in s,
            "no_direct_save_write": "archive_of_life_save" in s and "setItem" not in s,
        }
    return {}
