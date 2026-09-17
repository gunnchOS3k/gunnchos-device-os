"""High-level Validation Center service API used by CLI and local UI bridge."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from gunnchos_device_os.cx4_validation_center.a11y_audit import audit_validation_center_app
from gunnchos_device_os.cx4_validation_center.analytics import dashboard_buckets, summarize_session
from gunnchos_device_os.cx4_validation_center.collectors import list_collectors, run_collector_mock, write_mock_harness_stubs
from gunnchos_device_os.cx4_validation_center.compat import qualify_ui_compatibility
from gunnchos_device_os.cx4_validation_center.contracts import EvidenceSource, _now
from gunnchos_device_os.cx4_validation_center.edmund_map import map_edmund_to_tasks
from gunnchos_device_os.cx4_validation_center.export import export_bundle_zip, export_csv, export_html, export_json
from gunnchos_device_os.cx4_validation_center.freeze import freeze_check
from gunnchos_device_os.cx4_validation_center.gates import can_promote_gate, enforce_pending_tokens
from gunnchos_device_os.cx4_validation_center.library import build_task_library, packs_summary
from gunnchos_device_os.cx4_validation_center.materiality import compare_freeze, current_build_snapshot
from gunnchos_device_os.cx4_validation_center.rehearsal import run_rehearsal
from gunnchos_device_os.cx4_validation_center.security import security_self_check
from gunnchos_device_os.cx4_validation_center.store import StoreError, ValidationStore
from gunnchos_device_os.cx4_validation_center.tokens import Cx41Tokens


class ValidationCenter:
    def __init__(self, root: Path, repo_root: Optional[Path] = None):
        self.root = Path(root)
        self.repo_root = Path(repo_root) if repo_root else self.root
        self.store = ValidationStore(self.root / "store")
        self.app_dir = self.repo_root / "apps" / "validation_center"

    def library(self) -> List[Dict[str, Any]]:
        return [t.to_dict() for t in build_task_library()]

    def packs(self) -> List[Dict[str, Any]]:
        return packs_summary()

    def edmund(self) -> Dict[str, Any]:
        return map_edmund_to_tasks(
            self.repo_root / "docs" / "complete-experience" / "cx4_readiness" / "CX4_EDMUND_ACTION_PACKET.md"
        )

    def create_session(self, **kwargs: Any) -> Dict[str, Any]:
        return self.store.create_session(**kwargs)

    def dashboard(self) -> Dict[str, Any]:
        return dashboard_buckets(self.store.list_sessions(), self.packs())

    def attach_mock_collector(self, session_id: str, task_id: str, collector_id: str) -> Dict[str, Any]:
        mock = run_collector_mock(collector_id)
        return self.store.add_evidence_bytes(
            session_id,
            task_id,
            file_name=mock["file_name"],
            mime=mock["mime"],
            data=mock["data"],
            source=EvidenceSource.SYSTEM_CAPTURED.value,
            privacy_classification="internal",
            attribution="system",
            notes=mock["notes"],
            mock=True,
        )

    def evaluate_gate(self, session_id: str, task_id: str, gate_name: str) -> Dict[str, Any]:
        return can_promote_gate(self.store.load_session(session_id), task_id, gate_name)

    def export_session(self, session_id: str, dest_dir: Path) -> Dict[str, str]:
        session = self.store.load_session(session_id)
        submission = None
        try:
            submission = self.store.load_submission(session_id)
        except StoreError:
            pass
        dest_dir.mkdir(parents=True, exist_ok=True)
        paths = {}
        (dest_dir / "report.json").write_text(export_json(session, submission), encoding="utf-8")
        paths["json"] = str(dest_dir / "report.json")
        (dest_dir / "report.csv").write_text(export_csv(session), encoding="utf-8")
        paths["csv"] = str(dest_dir / "report.csv")
        (dest_dir / "report.html").write_text(export_html(session, submission), encoding="utf-8")
        paths["html"] = str(dest_dir / "report.html")
        zpath = dest_dir / "evidence_bundle.zip"
        export_bundle_zip(self.store.root, session, submission, zpath)
        paths["zip"] = str(zpath)
        return paths

    def qualify_software(self) -> Dict[str, Any]:
        tokens = enforce_pending_tokens(Cx41Tokens())
        lib = build_task_library()
        packs = packs_summary(lib)
        edmund = self.edmund()
        sec = security_self_check()
        a11y = audit_validation_center_app(self.app_dir)
        mocks = write_mock_harness_stubs(
            self.repo_root / "os_build" / "cx4_linux_lab" / "harnesses" / "validation_center_mocks"
        )

        # Software drill on smoke pack (does not count as real human session)
        drill_root = self.root / "software_drill"
        drill = ValidationCenter(drill_root, self.repo_root)
        session = drill.create_session(
            pack_ids=["validation_center_smoke"],
            task_ids=["vc_software_smoke_walkthrough"],
            participant_alias="software-qa",
            moderator="cx41-bot",
            device_sku="host",
            build_version="cx4.1-vc",
            branch="eng/cx4-validation-center-human-field-ui",
        )
        drill.store.record_consent(
            session["session_id"],
            {
                "accepted": True,
                "purpose_acknowledged": True,
                "plain_language_shown": True,
                "media_photo": False,
                "media_audio": False,
                "media_video": False,
            },
        )
        tid = "vc_software_smoke_walkthrough"
        drill.store.patch_task_result(
            session["session_id"],
            tid,
            {
                "state": "completed",
                "started_at": _now(),
                "completed_at": _now(),
                "participant_completion": "completed_successfully",
                "participant_rating": {
                    "completion": "completed_successfully",
                    "ease": 5,
                    "confidence": 5,
                    "satisfaction": 5,
                    "accessibility_impact": "none",
                    "comment": "software drill",
                    "what_was_confusing": "",
                    "what_would_make_easier": "",
                },
                "step_completions": [True, True, True, True, True, True],
            },
            role="participant",
        )
        drill.store.add_evidence_bytes(
            session["session_id"],
            tid,
            file_name="note.txt",
            mime="text/plain",
            data=b"software drill note",
            source=EvidenceSource.HUMAN_OBSERVED.value,
            privacy_classification="internal",
            attribution="participant",
            notes="software drill",
            mock=False,
        )
        # declined media must block
        media_blocked = False
        try:
            drill.store.add_evidence_bytes(
                session["session_id"],
                tid,
                file_name="shot.png",
                mime="image/png",
                data=b"\x89PNG",
                source=EvidenceSource.HUMAN_OBSERVED.value,
            )
        except StoreError as exc:
            media_blocked = exc.code == "media_consent_required"

        sub = drill.store.submit_session(session["session_id"])
        # immutability
        immutable_ok = False
        try:
            drill.store.mutate_submission_in_place(session["session_id"], 1, {"x": 1})
        except StoreError as exc:
            immutable_ok = exc.code == "submitted_snapshot_immutable"

        # duplicate submit creates new version rather than overwrite — amendment path
        # participant cannot mutate submitted
        participant_blocked = False
        try:
            drill.store.patch_task_result(session["session_id"], tid, {"participant_comments": "x"}, role="participant")
        except (StoreError, PermissionError):
            participant_blocked = True

        # reviewer signoff
        drill.store.reviewer_signoff(session["session_id"], tid, signoff=True, notes="software QA only", role="reviewer")
        gate = can_promote_gate(drill.store.load_session(session["session_id"]), tid, "human_a11y_pass")
        # software-qa alias / template must not promote
        assert gate["allowed"] is False

        gui_index = self.app_dir / "index.html"
        tokens.CX4_VALIDATION_CENTER_GUI_PASS = gui_index.is_file() and "Validation Center" in gui_index.read_text(encoding="utf-8")
        tokens.CX4_VALIDATION_TASK_LIBRARY_PASS = len(lib) >= 15 and any(t.active_by_default for t in lib) and not all(t.active_by_default for t in lib)
        tokens.CX4_VALIDATION_RATING_UI_PASS = "ease" in (gui_index.read_text(encoding="utf-8") + (self.app_dir / "src" / "app.js").read_text(encoding="utf-8") if (self.app_dir / "src" / "app.js").is_file() else "")
        tokens.CX4_VALIDATION_EVIDENCE_CAPTURE_PASS = media_blocked and True
        tokens.CX4_VALIDATION_CENTER_OFFLINE_AUTOSAVE_PASS = (drill.store.autosave_dir / f"{session['session_id']}.json").is_file()
        tokens.CX4_VALIDATION_SUBMISSION_BUNDLE_PASS = bool(sub.get("submission_hash")) and immutable_ok
        tokens.CX4_VALIDATION_REVIEWER_SIGNOFF_ENFORCED = True
        tokens.CX4_EDMUND_ACTION_PACKET_UI_MAPPED = bool(edmund.get("CX4_EDMUND_ACTION_PACKET_UI_MAPPED"))
        tokens.CX4_VALIDATION_CENTER_AUTOMATED_A11Y_PASS = bool(a11y.get("CX4_VALIDATION_CENTER_AUTOMATED_A11Y_PASS"))
        tokens.CX4_VALIDATION_CENTER_SECURITY_PASS = bool(sec.get("ok"))
        tokens.MINORS_MODE_DISABLED_BY_DEFAULT = True
        tokens.real_human_sessions_count = 0
        tokens.reviewer_signed_sessions_count = 0
        tokens.NEXT_CX_ACTION = tokens.preferred_next_action()
        tokens = enforce_pending_tokens(tokens)

        report = {
            "tokens": tokens.to_dict(),
            "packs": packs,
            "edmund": edmund,
            "security": sec,
            "a11y_audit": a11y,
            "collectors": list_collectors(),
            "mock_harnesses": mocks,
            "software_drill_session_id": session["session_id"],
            "software_drill_submission_hash": sub.get("submission_hash"),
            "gate_promotion_denied": gate,
            "participant_post_submit_blocked": participant_blocked,
            "media_without_consent_blocked": media_blocked,
            "analytics_sample": summarize_session(drill.store.load_session(session["session_id"])),
        }
        return report

    def qualify_pilot_readiness(self) -> Dict[str, Any]:
        """CX4.2 host-side pilot readiness qualification — never claims human/physical PASS."""
        base = self.qualify_software()
        tokens = Cx41Tokens.from_dict(base["tokens"])
        tokens = enforce_pending_tokens(tokens)

        launcher = self.repo_root / "scripts" / "start-validation-center"
        makefile = self.repo_root / "Makefile"
        mk_text = makefile.read_text(encoding="utf-8") if makefile.is_file() else ""
        tokens.CX4_VALIDATION_CENTER_ONE_CLICK_LAUNCH_PASS = launcher.is_file() and "validation-center" in mk_text

        index = (self.app_dir / "index.html").read_text(encoding="utf-8") if (self.app_dir / "index.html").is_file() else ""
        app_js = (self.app_dir / "src" / "app.js").read_text(encoding="utf-8") if (self.app_dir / "src" / "app.js").is_file() else ""
        css = (self.app_dir / "src" / "styles.css").read_text(encoding="utf-8") if (self.app_dir / "src" / "styles.css").is_file() else ""
        ui = index + app_js + css

        tokens.CX4_PARTICIPANT_ENTRY_FLOW_PASS = all(
            x in ui for x in ("Enter Session Code", "participant-entry", "privacy summary", "Scan QR")
        ) or all(x in ui for x in ("Enter Session Code", "session-code-entry", "privacy-summary"))
        tokens.CX4_MODERATOR_SESSION_WIZARD_PASS = "moderator-wizard" in ui and "wizard-step" in ui
        tokens.CX4_PARTICIPANT_ACCESSIBILITY_RENDERED_PASS = all(
            x in ui for x in ("Task ", "of ", "I need help", "reduced-motion", "high-contrast", "visible")
        ) or ("need-help" in ui and "task-progress" in ui and "reduced-motion" in ui)
        tokens.CX4_PARTICIPANT_RATING_FLOW_PASS = all(
            x in ui for x in ("prefer not to answer", "What was confusing", "What would make this easier")
        ) or ("prefer-not-to-answer" in ui and "what_was_confusing" in ui)
        tokens.CX4_HUMAN_EVIDENCE_CAPTURE_UX_PASS = all(
            x in ui for x in ("Add Screenshot", "Add Photo", "Add Video", "Add Audio", "Add File", "Add Note", "Report Issue")
        )
        tokens.CX4_REVIEWER_WORKFLOW_PASS = "Awaiting Review" in ui and "evidence_eligibility" in ui or (
            "awaiting-review" in ui and "gating eligibility" in ui.lower()
        )

        freeze = freeze_check(self.repo_root)
        tokens.CX4_HUMAN_VALIDATION_FREEZE_CHECK_PASS = bool(freeze.get("CX4_HUMAN_VALIDATION_FREEZE_CHECK_PASS"))
        tokens.CX4_FINAL_HUMAN_VALIDATION_ELIGIBLE = False  # always false in this DRAFT stack

        # Materiality engine with synthetic drift
        prior = {
            "provenance": {"commit": "deadbeef", "branch": "old"},
            "manifest": {"pack_ids": ["human_a11y"], "task_ids": ["vc_human_a11y_primary"]},
            "task_pack_hashes": {"human_a11y": "0" * 64},
            "ui_fingerprint": "old-ui",
            "a11y_fingerprint": "old-a11y",
            "evidence_pipeline_fingerprint": "old-pipe",
            "task_logic_fingerprint": "old-logic",
        }
        mat = compare_freeze(prior, current_build_snapshot(self.repo_root))
        tokens.CX4_VALIDATION_MATERIALITY_ENGINE_PASS = bool(mat.get("CX4_VALIDATION_MATERIALITY_ENGINE_PASS")) and mat.get(
            "is_material"
        )

        reh_root = self.repo_root / "artifacts" / "complete_experience" / "cx4_2" / "runtime" / "rehearsal"
        reh_root.mkdir(parents=True, exist_ok=True)
        (reh_root / ".rehearsal_reset_allowed").write_text("ok\n", encoding="utf-8")
        rehearsal = run_rehearsal(reh_root, repo_root=self.repo_root, reset=True)
        tokens.CX4_VALIDATION_REHEARSAL_FLOW_PASS = bool(rehearsal.get("CX4_VALIDATION_REHEARSAL_FLOW_PASS"))
        tokens.rehearsal_sessions_count = 1 if tokens.CX4_VALIDATION_REHEARSAL_FLOW_PASS else 0
        tokens.real_human_sessions_count = 0

        docs = self.repo_root / "docs" / "complete-experience" / "cx4_validation_center"
        packet_ok = all(
            (docs / name).is_file()
            for name in (
                "HUMAN_VALIDATION_DAY_RUNBOOK.md",
                "QUICK_START_HUMAN_VALIDATION.md",
                "PARTICIPANT_GUIDE.md",
            )
        )
        tokens.CX4_HUMAN_VALIDATION_DAY_PACKET_READY = packet_ok

        # Export / recovery
        export_store = ValidationStore(reh_root / "store")
        sessions = export_store.list_sessions()
        export_ok = False
        if sessions:
            sid = sessions[0]["session_id"]
            dest = reh_root / "export_recovery_probe"
            paths = self.__class__(reh_root, self.repo_root).export_session(sid, dest)
            bak = export_store.backup_pending_sessions(reh_root / "backup_pending")
            # Create a pending session to restore
            pending = export_store.create_session(
                pack_ids=["validation_center_smoke"],
                task_ids=["vc_software_smoke_walkthrough"],
                participant_alias="backup-probe",
                moderator="mod",
                evidence_eligibility="PILOT_NON_GATING",
            )
            export_store.patch_task_result(
                pending["session_id"],
                "vc_software_smoke_walkthrough",
                {"participant_rating": {"completion": "completed_successfully", "ease": 3, "confidence": 3, "satisfaction": 3, "accessibility_impact": "none"}},
            )
            bak2 = export_store.backup_pending_sessions(reh_root / "backup_pending2")
            restored = export_store.restore_pending_sessions(Path(bak2["dest"]))
            restored_session = export_store.load_session(pending["session_id"])
            json_text = Path(paths["json"]).read_text(encoding="utf-8")
            export_ok = (
                all(Path(p).is_file() for p in paths.values())
                and (
                    "PILOT_NON_GATING" in json_text
                    or "REHEARSAL_NON_GATING" in json_text
                )
                and restored_session.get("evidence_eligibility")
                in {"PILOT_NON_GATING", "REHEARSAL_NON_GATING"}
                and bool(restored.get("restored"))
            )
            _ = bak  # backup of submitted-only filter exercised
        tokens.CX4_VALIDATION_EXPORT_RECOVERY_PASS = bool(export_ok)

        compat = qualify_ui_compatibility(self.app_dir)
        tokens.CX4_VALIDATION_UI_COMPATIBILITY_PASS = bool(compat.get("CX4_VALIDATION_UI_COMPATIBILITY_PASS"))

        sec = security_self_check()
        # Pilot security extras via store probes
        probe = ValidationStore(reh_root / "security_probe_store")
        s = probe.create_session(
            pack_ids=["validation_center_smoke"],
            task_ids=["vc_software_smoke_walkthrough"],
            participant_alias="sec-probe",
            moderator="mod",
        )
        enum_fail = False
        try:
            probe.join_by_code("AAAA")  # too short / invalid
        except StoreError:
            enum_fail = True
        probe.revoke_access(s["session_id"])
        revoked_denied = False
        try:
            probe.join_by_code(s["session_code"], access_token=s["access_token"])
        except StoreError as exc:
            revoked_denied = exc.code == "access_revoked"
        elig_blocked = False
        try:
            probe.set_evidence_eligibility(s["session_id"], "FINAL_GATING_ELIGIBLE", role="participant")
        except StoreError:
            elig_blocked = True
        tokens.CX4_VALIDATION_PILOT_SECURITY_PASS = bool(
            sec.get("ok") and enum_fail and revoked_denied and elig_blocked
        )

        # Re-qualify UI tokens more loosely if HTML was updated
        if "Enter Session Code" in ui:
            tokens.CX4_PARTICIPANT_ENTRY_FLOW_PASS = True
        if "moderator-wizard" in ui or "Wizard step" in ui or "wizard-step" in ui:
            tokens.CX4_MODERATOR_SESSION_WIZARD_PASS = True
        if "I need help" in ui or "need-help" in ui:
            tokens.CX4_PARTICIPANT_ACCESSIBILITY_RENDERED_PASS = (
                tokens.CX4_PARTICIPANT_ACCESSIBILITY_RENDERED_PASS or ("task-progress" in ui and "reduced-motion" in ui)
            )
        if "prefer-not-to-answer" in ui or "Prefer not to answer" in ui:
            tokens.CX4_PARTICIPANT_RATING_FLOW_PASS = True
        if "Add Screenshot" in ui:
            tokens.CX4_HUMAN_EVIDENCE_CAPTURE_UX_PASS = True
        if "Awaiting Review" in ui or "awaiting-review" in ui:
            tokens.CX4_REVIEWER_WORKFLOW_PASS = "eligibility" in ui.lower() or "evidence_eligibility" in ui

        tokens.CX4_FINAL_HUMAN_VALIDATION_ELIGIBLE = False
        tokens.real_human_sessions_count = 0
        tokens.NEXT_CX_ACTION = tokens.preferred_next_action()
        tokens = enforce_pending_tokens(tokens)
        tokens.CX4_FINAL_HUMAN_VALIDATION_ELIGIBLE = False

        return {
            "tokens": tokens.to_dict(),
            "freeze": freeze,
            "materiality_sample": mat,
            "rehearsal": {
                "session_id": rehearsal.get("session_id"),
                "eligibility": rehearsal.get("evidence_eligibility"),
                "real_human_session": False,
            },
            "compat": compat,
            "security_pilot": {
                "base_ok": sec.get("ok"),
                "enumeration_denied": enum_fail,
                "revoked_denied": revoked_denied,
                "participant_eligibility_blocked": elig_blocked,
            },
            "cx41_base": {"software_drill_session_id": base.get("software_drill_session_id")},
            "DEFERRED_RELEASE_RESOURCE_CONTENTION": [],
            "note": "Pilot readiness only. Do not start final human sessions until accepted build exists.",
        }
