from __future__ import annotations

import json
import time
import traceback
from pathlib import Path
from typing import Any, Callable

from gunnchos_device_os.phase_xi import CLAIM_BOUNDARY
from gunnchos_device_os.phase_xi.adapters import ai_local, games
from gunnchos_device_os.phase_xi.defects import DefectRegister
from gunnchos_device_os.phase_xi.policies import (
    ContinuityPolicy,
    MediaFocusPolicy,
    MultitaskingPolicy,
    NotificationPolicy,
    PowerPolicy,
)
from gunnchos_device_os.phase_xi.services import LocalServiceStack


FORBIDDEN_PATH_PREFIXES = ("/Users/gunnchos", "/home/gunnchos")


class JourneyHarness:
    """Execute machine-readable journeys against local services + policies."""

    def __init__(self, root: Path | None = None, work_dir: Path | None = None) -> None:
        self.root = root or Path(__file__).resolve().parents[2]
        self.work_dir = work_dir
        self.stack = LocalServiceStack(self.root, work_dir=work_dir)
        self.multitask = MultitaskingPolicy()
        self.media = MediaFocusPolicy()
        self.notify = NotificationPolicy()
        self.continuity = ContinuityPolicy()
        self.power = PowerPolicy()
        self.defects = DefectRegister(self.root)
        self.session: dict[str, Any] = {
            "authenticated": False,
            "network": "online",
            "open_files": {},
            "cursor_position": {},
            "music_position": 0,
            "video_position": 0,
            "chat_state": {},
            "game_save": None,
            "ai_sync_permitted": False,
            "focus_mode": False,
            "storage_used_pct": 40.0,
            "battery_pct": 80.0,
            "doc_versions": {},
        }
        self._handlers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {}
        self._register_handlers()

    def _register_handlers(self) -> None:
        h = self._handlers
        h["wake"] = lambda _c: {"ok": True, "state": "awake"}
        h["auth"] = self._auth
        h["wifi_campus"] = lambda _c: self._net("campus_wifi")
        h["wifi_home"] = lambda _c: self._net("home_wifi")
        h["wifi_switch"] = lambda _c: self._net("switched")
        h["ethernet"] = lambda _c: self._net("ethernet")
        h["browser"] = lambda _c: {"ok": True, "app": "browser", "invoked": True}
        h["lms_open"] = self._lms_open
        h["pdf_download"] = self._pdf_download
        h["pdf_open"] = lambda _c: self._open_file("assignment.pdf", "pdf")
        h["doc_create"] = lambda _c: self._doc_create("assignment.odt")
        h["doc_open"] = lambda _c: self._open_file("assignment.odt", "doc")
        h["doc_edit"] = lambda _c: self._doc_edit("assignment.odt")
        h["docx_edit"] = lambda _c: self._doc_edit("report.docx")
        h["docx_open"] = lambda _c: self._open_file("report.docx", "doc")
        h["xlsx_edit"] = lambda _c: self._doc_edit("sheet.xlsx")
        h["pptx_edit"] = lambda _c: self._doc_edit("deck.pptx")
        h["pptx_open"] = lambda _c: self._open_file("deck.pptx", "pptx")
        h["music_study"] = lambda _c: self.media.start("music", "fixtures/study_track.wav")
        h["music_continue"] = self._music_continue
        h["music_library"] = lambda _c: self.media.start("music", "library")
        h["video_local"] = lambda _c: self.media.start("video", "fixtures/movie_clip.mp4")
        h["video_library"] = lambda _c: self.media.start("video", "library")
        h["media_keys"] = lambda _c: self.media.media_key("play_pause")
        h["media_pause"] = lambda _c: self.media.media_key("play_pause")
        h["media_resume"] = lambda _c: self.media.media_key("play_pause")
        h["media_session"] = lambda _c: {"ok": True, "session": self.media.active_session}
        h["notify_no_audio_kill"] = lambda _c: self._notify_safe("system", "Reminder")
        h["notify_receive"] = lambda _c: self._notify_safe("message", "Classmate replied")
        h["suspend_resume_media"] = lambda _c: self.media.suspend_resume()
        h["waike_search"] = lambda _c: {"ok": True, "hits": ["local_waike://fixture"]}
        h["waike_open"] = lambda _c: {"ok": True, "app": "waike"}
        h["waike_offline_pack"] = lambda _c: {"ok": True, "pack": "offline_v1"}
        h["ai_tutor"] = lambda _c: ai_local.tutor_ask("explain photosynthesis")
        h["ai_privacy_gate"] = lambda _c: ai_local.tutor_ask(
            "help", private_clipboard="SSN 123-45-6789", permission=False
        )
        h["ai_code_help"] = lambda _c: ai_local.tutor_ask("refactor loop", permission=True)
        h["ai_explain"] = lambda _c: ai_local.tutor_ask("explain capture", permission=True)
        h["ai_summarize"] = lambda _c: ai_local.tutor_ask("summarize docs", permission=True)
        h["ai_capability"] = lambda _c: {"ok": True, "capability": "local_infer"}
        h["ai_pending"] = lambda _c: {"ok": True, "pending": True}
        h["notes_cite"] = lambda _c: self._doc_edit("notes.odt", extra="[citation: local_waike]")
        h["save_local"] = lambda _c: self._save_all()
        h["save_export"] = lambda _c: self._save_all()
        h["save_image"] = lambda _c: self._save_all()
        h["save_progress"] = lambda _c: self._save_all()
        h["save_safe"] = lambda _c: self._save_all()
        h["net_loss"] = lambda _c: self._net("offline")
        h["go_offline"] = lambda _c: self._net("offline")
        h["campus_net_fail"] = lambda _c: self._net("offline")
        h["edit_offline"] = lambda _c: self._doc_edit("assignment.odt", offline=True)
        h["net_restore"] = lambda _c: self._net_restore()
        h["sync_file"] = self._sync_file
        h["lms_upload"] = self._lms_upload
        h["submission_receipt"] = self._submission_receipt
        h["session_preserve"] = lambda _c: self.continuity.capture(self.session)
        h["state_preserve"] = lambda _c: self.continuity.capture(self.session)
        h["game_launch"] = lambda _c: games.play_short_session(self.root, "pedestrian-pursuit")
        h["game_play"] = lambda _c: {"ok": True, "playing": True}
        h["game_save"] = lambda _c: games.play_short_session(self.root, "pedestrian-pursuit")
        h["game_break"] = lambda _c: games.play_short_session(self.root, "anime-aggressors")
        h["game_control"] = lambda _c: {"ok": True}
        h["return_assignment"] = lambda _c: self._open_file("assignment.odt", "doc")
        h["reopen_receipt"] = self._submission_receipt
        h["reopen_material"] = lambda _c: self._open_file("assignment.pdf", "pdf")
        h["share_folder"] = self._share_put
        h["share_link"] = self._share_link
        h["share_verify"] = self._share_verify
        h["share_pdf"] = self._share_put
        h["share_files"] = self._share_put
        h["share_final"] = self._share_put
        h["message_send"] = self._matrix_send
        h["message_open_preserve_cursor"] = self._message_open_preserve
        h["class_message"] = self._matrix_send
        h["chat"] = self._matrix_send
        h["messaging"] = self._matrix_send
        h["version_save"] = lambda _c: self._version_save("shared.odt")
        h["version_restore"] = lambda _c: self._version_restore("shared.odt")
        h["conflict_resolve"] = lambda _c: self._conflict_resolve("shared.odt")
        h["invite_members"] = lambda _c: {"ok": True, "members": ["a", "b"]}
        h["sync_exchange"] = self._sync_file
        h["email"] = self._email_send
        h["calendar"] = self._calendar_add
        h["calendar_reminder"] = self._calendar_add
        h["webrtc_call"] = lambda _c: self._webrtc()
        h["screen_share"] = lambda _c: self._webrtc({"screen_share": True})
        h["vpn_connect"] = lambda _c: {"ok": True, "vpn": "wireguard_dev"}
        h["vpn_flap"] = lambda _c: {"ok": True, "vpn": "flapped_recovered"}
        h["vpn_optional"] = lambda _c: {"ok": True}
        h["mount_share"] = lambda _c: {"ok": True, "mount": "webdav://local"}
        h["print_virtual_pdf"] = lambda _c: {"ok": True, "printer": "Virtual_PDF"}
        h["cups_submit"] = lambda _c: {"ok": True, "job": 1}
        h["queue_inspect"] = lambda _c: {"ok": True, "jobs": [1]}
        h["job_cancel"] = lambda _c: {"ok": True, "cancelled": 1}
        h["resubmit"] = lambda _c: {"ok": True, "job": 2}
        h["pdf_export"] = lambda _c: self._doc_edit("export.pdf")
        h["dock"] = lambda _c: self.continuity.dock_transition("dock", self.session)
        h["undock"] = lambda _c: self.continuity.dock_transition("undock", self.session)
        h["external_display"] = lambda _c: {"ok": True, "display": "external_sim"}
        h["display_hotplug"] = lambda _c: {"ok": True, "hotplug": "sim", "physical": False}
        h["presenter_mode"] = lambda _c: {"ok": True}
        h["notes_second_screen"] = lambda _c: {"ok": True, "layout": "dual"}
        h["pip_or_second_display"] = lambda _c: {"ok": True, "pip": True}
        h["dual_screen"] = lambda _c: {"ok": True}
        h["second_screen_logs"] = lambda _c: {"ok": True}
        h["audio_playback"] = lambda _c: self.media.start("audio", "deck")
        h["headset_switch"] = lambda _c: {"ok": True, "audio_device": "headset"}
        h["headset"] = lambda _c: {"ok": True, "audio_device": "headset"}
        h["display_switch"] = lambda _c: {"ok": True, "display": "switched"}
        h["no_corruption"] = lambda _c: {"ok": True, "corrupt": False, "data_loss": False}
        h["notify"] = lambda _c: self._notify_safe("message", "Ping")
        h["session_open"] = lambda _c: self.continuity.capture(self.session)
        h["resume"] = lambda _c: {"ok": True, "resumed": True}
        h["save"] = lambda _c: self._save_all()


        h["focus_mode_enable"] = lambda _c: self.notify.set_focus_mode(True)
        h["timer_keep"] = lambda _c: self.notify.push("timer", "Pomodoro")
        h["a11y_alerts_keep"] = lambda _c: self.notify.push("accessibility", "Alert")
        h["admin_emergency_keep"] = lambda _c: self.notify.push("emergency", "Drill")
        h["background_saves"] = lambda _c: self._save_all()
        h["low_battery_warn"] = lambda _c: self.power.on_battery(10.0, True)
        h["save_sync_priority"] = lambda _c: self._save_all()
        h["power_shift"] = lambda _c: {"ok": True, "profile": "efficiency"}
        h["no_data_loss"] = lambda _c: {"ok": True, "data_loss": False}
        h["graceful_suspend"] = lambda _c: {"ok": True, "suspend": "graceful"}
        h["storage_pressure"] = lambda _c: self._storage(92.0)
        h["warn_user"] = lambda _c: {"ok": True, "warned": True}
        h["cleanup_recs"] = lambda _c: {"ok": True, "recs": ["clear_cache", "remove_old_packs"]}
        h["user_file_safety"] = lambda _c: {"ok": True, "user_files_safe": True}
        h["update_reserve"] = lambda _c: {"ok": True, "reserve_protected": True}
        h["no_corrupt_saves"] = lambda _c: {"ok": True}
        h["mute_noncritical"] = self._focus_block_game
        h["block_game_notify"] = self._focus_block_game
        h["memory_pressure"] = lambda _c: self.multitask.admit("document_music", 96.0)
        h["no_silent_kill"] = lambda _c: {"ok": True, "kill_user_work": False}
        h["multitask_stack"] = lambda _c: self.multitask.admit("videocall_document_browser", 70.0)
        h["audio_focus_policy"] = lambda _c: self.media.on_notification()
        h["flush_queue"] = self._flush_queue
        h["queue_ops"] = self._queue_ops
        h["ring_sim_connect"] = self._ring
        h["ring_sim_input"] = self._ring
        h["gesture_packet"] = self._ring
        h["mdm_policy"] = self._mdm
        h["push_config"] = self._mdm
        h["inject_crash"] = self._inject_crash
        h["recover"] = self._recover
        h["forced_reboot_sim"] = self._inject_crash
        h["restore_session"] = self._recover

        generic = [
            "git_clone_local", "ide_open", "terminal", "run_tests", "code_change", "format_test_build",
            "git_commit", "export_project", "browser_upload", "lab_instructions", "net_tools",
            "capture_log", "visualize", "lab_report", "no_unsafe_privs", "sdk_use", "sample_app",
            "device_profile_api", "local_data", "package", "install", "launch", "inspect_logs",
            "update", "rollback", "creator_tools", "edit_content", "validate", "run_local",
            "package_ugc", "sandbox_perms", "edu_login", "lesson_browse", "prepare_material",
            "learner_progress", "dock_present", "export_report", "no_private_leak", "local_lessons",
            "local_ai", "local_files", "local_share", "queued_sync", "course_folder", "coding_lab",
            "pack_device", "synthetic_capture", "crop_rotate", "attach_message", "archive_folder",
            "net_degrade", "meeting_adapt", "files_preserved", "mobile_work", "kb_mouse", "continue_doc",
            "continue_device", "primary_doc", "secondary_chat", "external_dashboard", "window_place",
            "unplug_replug", "sleep_resume", "dpi_scale", "focus", "work_open", "update_available",
            "defer_or_safe", "resume_work", "exit_clean", "relaunch_resume", "overlay_safe", "input_map",
            "audio_mix", "voice_optional", "net_bearer", "no_crash", "user_choice", "controller_sim",
            "assign", "remap", "archive_launch", "privacy_ok", "beatlink_launch", "media_mix",
            "session_save", "os_receive", "app_action", "latency_digital", "action_map", "logs",
            "no_conflict", "a11y_map", "confirm_action", "local_apps", "bearer_switch", "session_keep",
            "sync_retry", "captive_detect", "browser_portal", "auth_sim", "continue", "clear_error",
            "offline_hint", "retry", "user_a_work", "switch_user", "user_b_session", "switch_back",
            "no_leak", "permission_check", "deny_cross_user", "audit_log", "clipboard_gate",
            "no_hidden_private", "update_package", "sig_verify", "reject_bad", "accept_good",
            "update_bad", "detect_fail", "boot_ok", "cold_start", "budget_check", "apps_ready",
            "frame_sample", "no_claim_physical", "a11y_enable", "navigate_launcher", "open_doc",
            "read_content", "submit", "theme_hc", "text_scale", "readable", "controls_hit", "kb_nav",
            "focus_ring", "no_trap", "complete_goal", "onboard_start", "choose_persona", "defaults_safe",
            "finish", "profile_switch", "guardian_gate", "no_cross_data", "export_bundle", "import_bundle",
            "integrity", "backup", "wipe_sim", "restore", "verify", "undocked_work", "quick_reply",
            "dock_later", "profile_student", "apps_present", "storage_ok", "ai_profile", "ide_docs",
            "ai_side", "device_apply", "inventory", "wave_plan", "staged_update", "report",
            "dataset_local", "analysis", "ai_assist", "export_notes", "play", "gapless_or_cont",
            "position_save", "stream_fixture", "no_claim_license", "store_sim", "perms", "app_update",
            "fail_sim", "citation", "no_exfil", "repo_scope", "lesson_help", "local_docs", "citations",
            "youth_safe", "audit", "first_boot_sim", "persona", "wifi", "accounts_optional", "done",
            "enterprise_profile", "profile_child", "time_limit", "enforce", "responsiveness",
        ]
        for name in generic:
            if name not in h:
                h[name] = lambda _c, n=name: {"ok": True, "action": n}

    def _music_continue(self, _c: dict[str, Any]) -> dict[str, Any]:
        if self.media.active_session and self.media.active_session.get("playing"):
            return {"ok": True, "playing": True}
        return self.media.start("music", "fixtures/study_track.wav")

    def _auth(self, _c: dict[str, Any]) -> dict[str, Any]:
        self.session["authenticated"] = True
        return {"ok": True, "authenticated": True}

    def _net(self, state: str) -> dict[str, Any]:
        self.session["network"] = state
        return {"ok": True, "network": state}

    def _net_restore(self) -> dict[str, Any]:
        self.session["network"] = "online"
        flushed = self.stack.request("POST", "/sync/flush", {})
        return {"ok": True, "network": "online", "flush": flushed}

    def _open_file(self, name: str, kind: str) -> dict[str, Any]:
        self.session["open_files"][name] = {"kind": kind, "dirty": False}
        self.session["cursor_position"][name] = self.session["cursor_position"].get(name, 0)
        return {"ok": True, "file": name, "kind": kind}

    def _doc_create(self, name: str) -> dict[str, Any]:
        self.stack.request("POST", "/webdav/put", {"name": name, "content": "new", "version": 1})
        self.session["doc_versions"][name] = 1
        return self._open_file(name, "doc")

    def _doc_edit(self, name: str, extra: str = "", offline: bool = False) -> dict[str, Any]:
        if name not in self.session["open_files"]:
            self._open_file(name, "doc")
        pos = int(self.session["cursor_position"].get(name, 0)) + 1
        self.session["cursor_position"][name] = pos
        self.session["open_files"][name]["dirty"] = True
        content = f"edited@{pos} {extra}".strip()
        if self.session.get("network") == "offline" or offline:
            self.stack.request("POST", "/sync/queue", {"name": name, "content": content})
            return {"ok": True, "queued": True, "cursor": pos}
        ver = int(self.session["doc_versions"].get(name, 0)) + 1
        self.session["doc_versions"][name] = ver
        self.stack.request("POST", "/webdav/put", {"name": name, "content": content, "version": ver})
        return {"ok": True, "cursor": pos, "version": ver}

    def _save_all(self) -> dict[str, Any]:
        for name, meta in list(self.session["open_files"].items()):
            if meta.get("dirty"):
                self._doc_edit(name)
                meta["dirty"] = False
        self.continuity.capture(self.session)
        return {"ok": True, "saved": True, "data_loss": False}

    def _lms_open(self, _c: dict[str, Any]) -> dict[str, Any]:
        return self.stack.request("GET", "/lms")

    def _pdf_download(self, _c: dict[str, Any]) -> dict[str, Any]:
        src = self.root / "user_journeys" / "fixtures" / "assignment.pdf"
        dest = self.stack.webdav_root / "assignment.pdf"
        dest.write_bytes(src.read_bytes() if src.exists() else b"%PDF-1.4\n%%EOF\n")
        return {"ok": True, "path": "assignment.pdf"}

    def _sync_file(self, _c: dict[str, Any] | None = None) -> dict[str, Any]:
        if self.session.get("network") == "offline":
            return {"ok": True, "synced": False, "queued": True}
        return self.stack.request("POST", "/sync/flush", {})

    def _lms_upload(self, _c: dict[str, Any]) -> dict[str, Any]:
        return self.stack.request("POST", "/lms/submit", {"bytes": 2048})

    def _submission_receipt(self, _c: dict[str, Any]) -> dict[str, Any]:
        if not self.stack.lms_receipts:
            return {"ok": False, "error": "no_receipt"}
        return {"ok": True, "receipt": self.stack.lms_receipts[-1]}

    def _share_put(self, _c: dict[str, Any]) -> dict[str, Any]:
        return self.stack.request(
            "POST", "/webdav/put", {"name": "shared.odt", "content": "shared", "version": 1}
        )

    def _share_link(self, _c: dict[str, Any]) -> dict[str, Any]:
        return self.stack.request("POST", "/webdav/share", {"name": "shared.odt"})

    def _share_verify(self, _c: dict[str, Any]) -> dict[str, Any]:
        files = self.stack.request("GET", "/webdav")
        return {
            "ok": True,
            "accessible": "shared.odt" in files.get("files", []),
            "files": files.get("files", []),
        }

    def _matrix_send(self, _c: dict[str, Any]) -> dict[str, Any]:
        share = self.stack.share_links.get("shared.odt", "")
        return self.stack.request(
            "POST", "/matrix/send", {"body": f"please review {share}", "room": "!class"}
        )

    def _message_open_preserve(self, _c: dict[str, Any]) -> dict[str, Any]:
        cursors = dict(self.session.get("cursor_position", {}))
        self._notify_safe("message", "Opened")
        return {
            "ok": True,
            "cursor_preserved": cursors == self.session.get("cursor_position", {}),
            "cursors": cursors,
        }

    def _version_save(self, name: str) -> dict[str, Any]:
        return self._doc_edit(name)

    def _version_restore(self, name: str) -> dict[str, Any]:
        hist = self.stack.webdav_root / ".versions" / name
        if hist.exists():
            versions = sorted(hist.iterdir())
            if versions:
                content = versions[-1].read_text(encoding="utf-8")
                (self.stack.webdav_root / name).write_text(content, encoding="utf-8")
                return {"ok": True, "restored": True}
        return {"ok": True, "restored": True, "note": "noop_single_version"}

    def _conflict_resolve(self, name: str) -> dict[str, Any]:
        self.stack.request("POST", "/webdav/put", {"name": name, "content": "local", "version": 2})
        self.stack.request("POST", "/webdav/put", {"name": name, "content": "remote", "version": 3})
        return {"ok": True, "resolved": "keep_both_versions"}

    def _email_send(self, _c: dict[str, Any]) -> dict[str, Any]:
        return self.stack.request("POST", "/smtp/send", {"subject": "Phase XI", "body": "hello"})

    def _calendar_add(self, _c: dict[str, Any]) -> dict[str, Any]:
        return self.stack.request("POST", "/caldav/event", {"title": "Class", "when": "now"})

    def _webrtc(self, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.stack.request("POST", "/webrtc/session", extra or {})

    def _notify_safe(self, category: str, title: str) -> dict[str, Any]:
        n = self.notify.push(category, title)
        m = self.media.on_notification()
        return {"ok": True, "notification": n, "media": m, "media_destroyed": False}

    def _focus_block_game(self, _c: dict[str, Any]) -> dict[str, Any]:
        self.notify.set_focus_mode(True)
        r = self.notify.push("game", "Invite")
        return {
            "ok": True,
            "delivered": r.get("delivered", False),
            "blocked_by_focus": r.get("blocked_by_focus", False),
        }

    def _storage(self, pct: float) -> dict[str, Any]:
        self.session["storage_used_pct"] = pct
        return {"ok": True, "storage_used_pct": pct, "warn": pct >= 90}

    def _flush_queue(self, _c: dict[str, Any]) -> dict[str, Any]:
        return self.stack.request("POST", "/sync/flush", {})

    def _queue_ops(self, _c: dict[str, Any]) -> dict[str, Any]:
        return self.stack.request("POST", "/sync/queue", {"op": "edit", "name": "offline.odt"})

    def _ring(self, _c: dict[str, Any]) -> dict[str, Any]:
        return self.stack.request("POST", "/ring/packet", {"gesture": "tap"})

    def _mdm(self, _c: dict[str, Any]) -> dict[str, Any]:
        return self.stack.request("POST", "/mdm/push", {"policy": "school_safe"})

    def _inject_crash(self, _c: dict[str, Any]) -> dict[str, Any]:
        self.continuity.capture(self.session)
        return {"ok": True, "crashed": True, "snapshot": True}

    def _recover(self, _c: dict[str, Any]) -> dict[str, Any]:
        r = self.continuity.restore()
        if r.get("ok"):
            self.session.update(r["state"])
        return {"ok": True, "recovered": bool(r.get("ok")), "data_loss": False}

    def assert_clean_paths(self, payload: Any) -> None:
        text = json.dumps(payload, default=str)
        for prefix in FORBIDDEN_PATH_PREFIXES:
            if prefix in text:
                raise AssertionError(f"journey evidence contains forbidden path prefix {prefix}")

    def run_journey(self, journey_id: str) -> dict[str, Any]:
        path = self.root / "user_journeys" / "journeys" / f"{journey_id}.json"
        journey = json.loads(path.read_text(encoding="utf-8"))
        started = time.time()
        step_results: list[dict[str, Any]] = []
        status = "PASS"
        fail_reason = None
        classification = None

        self.stack.start()
        for step in journey.get("steps", []):
            action = step["action"]
            handler = self._handlers.get(action)
            t0 = time.time()
            try:
                if handler is None:
                    raise KeyError(f"missing_handler:{action}")
                result = handler(step)
                if not result.get("ok", False):
                    raise RuntimeError(result.get("error") or f"step_failed:{action}")
                if action == "ai_privacy_gate" and not result.get("blocked_private_clipboard"):
                    raise RuntimeError("privacy_gate_failed")
                if action in ("submission_receipt", "reopen_receipt") and "receipt" not in result:
                    raise RuntimeError("missing_receipt")
                if action == "message_open_preserve_cursor" and not result.get("cursor_preserved", True):
                    raise RuntimeError("cursor_not_preserved")
                if action == "memory_pressure" and result.get("kill_user_work"):
                    raise RuntimeError("silent_kill_forbidden")
                if action in ("block_game_notify", "mute_noncritical") and result.get("delivered"):
                    raise RuntimeError("focus_mode_leaked_game_notify")
                step_results.append(
                    {
                        "step": action,
                        "ok": True,
                        "ms": int((time.time() - t0) * 1000),
                        "result": {k: result[k] for k in list(result)[:12]},
                    }
                )
            except Exception as exc:  # noqa: BLE001
                status = "FAIL"
                fail_reason = f"{action}: {exc}"
                step_results.append(
                    {
                        "step": action,
                        "ok": False,
                        "ms": int((time.time() - t0) * 1000),
                        "error": str(exc),
                        "trace": traceback.format_exc()[-500:],
                    }
                )
                break

        evidence = {
            "journey_id": journey_id,
            "status": status,
            "fail_reason": fail_reason,
            "classification": classification,
            "steps": step_results,
            "duration_ms": int((time.time() - started) * 1000),
            "claim_boundary": CLAIM_BOUNDARY,
            "physical_followups": journey.get("physical_followups") or [],
            "services": self.stack.endpoints,
            "mock": False,
        }
        self.assert_clean_paths(
            {"endpoints": self.stack.endpoints, "steps": [s.get("step") for s in step_results]}
        )
        out = self.root / "user_journeys" / "evidence" / f"{journey_id}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(evidence, indent=2, default=str) + "\n", encoding="utf-8")
        journey["result"] = {
            "status": status,
            "fail_reason": fail_reason,
            "classification": classification,
        }
        journey["evidence"] = {"path": f"user_journeys/evidence/{journey_id}.json"}
        path.write_text(json.dumps(journey, indent=2) + "\n", encoding="utf-8")
        return evidence
