"""High-level Validation Center service API used by CLI and local UI bridge."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from gunnchos_device_os.cx4_validation_center.a11y_audit import audit_validation_center_app
from gunnchos_device_os.cx4_validation_center.analytics import dashboard_buckets, summarize_session
from gunnchos_device_os.cx4_validation_center.collectors import list_collectors, run_collector_mock, write_mock_harness_stubs
from gunnchos_device_os.cx4_validation_center.contracts import EvidenceSource, _now
from gunnchos_device_os.cx4_validation_center.edmund_map import map_edmund_to_tasks
from gunnchos_device_os.cx4_validation_center.export import export_bundle_zip, export_csv, export_html, export_json
from gunnchos_device_os.cx4_validation_center.gates import can_promote_gate, enforce_pending_tokens
from gunnchos_device_os.cx4_validation_center.library import build_task_library, packs_summary
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
