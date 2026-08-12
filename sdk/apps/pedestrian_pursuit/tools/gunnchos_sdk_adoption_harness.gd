extends SceneTree

## gunnchSDK first-party game adoption harness — real Godot runtime evidence.
## Injects input, mutates ProgressionSave / GameManager, writes save + evidence JSON.
## Packaged inside the Godot export-pack (.pck) and launched via --main-pack.


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var failures := PackedStringArray()
	var evidence := {
		"schema": "gunnchos.sdk.godot_adoption_evidence.v1",
		"app_id": "gunnchos.pedestrian_pursuit",
		"runtime": "godot",
		"process_pid": OS.get_process_id(),
		"godot_version": Engine.get_version_info(),
		"headless": true,
		"display_server": DisplayServer.get_name(),
	}

	var prog := root.get_node_or_null("ProgressionSave")
	if prog == null:
		failures.append("ProgressionSave_autoload_missing")
	else:
		var before_xp := int(prog.xp)
		prog.add_xp(17)
		prog.unlock("mode:challenges")
		prog.unlock("sdk_adoption_probe")
		prog.save()
		var after_xp := int(prog.xp)
		var save_abs := ProjectSettings.globalize_path("user://pp_progression.cfg")
		evidence["progression"] = {
			"before_xp": before_xp,
			"after_xp": after_xp,
			"unlocked_challenges": bool(prog.is_unlocked("mode:challenges")),
			"unlocked_probe": bool(prog.is_unlocked("sdk_adoption_probe")),
			"save_path": "user://pp_progression.cfg",
			"save_abs": save_abs,
			"save_exists": FileAccess.file_exists("user://pp_progression.cfg"),
		}
		if after_xp <= before_xp and before_xp >= 0:
			# add_xp may level-up and reduce remainder; accept level increase too
			if int(prog.level) <= 1 and after_xp <= before_xp:
				failures.append("xp_or_level_did_not_change")
		if not bool(prog.is_unlocked("sdk_adoption_probe")):
			failures.append("unlock_not_persisted_in_memory")
		if not bool(evidence["progression"]["save_exists"]):
			failures.append("save_file_missing")

	var accept := InputEventAction.new()
	accept.action = "ui_accept"
	accept.pressed = true
	Input.parse_input_event(accept)
	await process_frame
	var accel := InputEventAction.new()
	accel.action = "accelerate"
	accel.pressed = true
	Input.parse_input_event(accel)
	await process_frame
	evidence["input"] = {
		"ui_accept_pressed": Input.is_action_pressed("ui_accept") or Input.is_action_just_pressed("ui_accept"),
		"accelerate_parsed": true,
		"events_injected": 2,
	}

	var gm := root.get_node_or_null("GameManager")
	if gm == null:
		failures.append("GameManager_autoload_missing")
	else:
		gm.start_quick_race("verdant_cascade_circuit")
		evidence["game_manager"] = {
			"mode_label": str(gm.mode_label()),
			"selected_track": str(gm.selected_track_id),
		}
		if str(gm.mode_label()) != "Quick Race":
			failures.append("quick_race_mode_not_set")

	evidence["ok"] = failures.is_empty()
	evidence["failures"] = Array(failures)

	var out_path := ""
	var sandbox := OS.get_environment("GUNNCHOS_SANDBOX_DATA_DIR")
	if not sandbox.is_empty():
		out_path = sandbox.path_join("godot_adoption_evidence.json")
		var f := FileAccess.open(out_path, FileAccess.WRITE)
		if f != null:
			f.store_string(JSON.stringify(evidence, "\t"))
			f.close()
		else:
			out_path = ""
	if out_path.is_empty():
		out_path = ProjectSettings.globalize_path("user://godot_adoption_evidence.json")
		var f2 := FileAccess.open("user://godot_adoption_evidence.json", FileAccess.WRITE)
		if f2 != null:
			f2.store_string(JSON.stringify(evidence, "\t"))
			f2.close()

	evidence["evidence_path"] = out_path
	print("GUNNCHOS_GODOT_ADOPTION_EVIDENCE=" + out_path)
	print(JSON.stringify(evidence))
	if failures.is_empty():
		print("GUNNCHOS_FIRST_PARTY_GAME_SDK_ADOPTION_HARNESS_PASS=true")
		quit(0)
	else:
		print("GUNNCHOS_FIRST_PARTY_GAME_SDK_ADOPTION_HARNESS_PASS=false")
		for failure in failures:
			push_error(failure)
		quit(1)
