"""Local-first Validation Center store: autosave, immutable submissions, offline recovery."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from gunnchos_device_os.cx4_validation_center.contracts import (
    EvidenceItem,
    EvidenceSource,
    SessionStatus,
    ValidationSession,
    ValidationSubmission,
    ValidationTaskResult,
    _now,
    new_id,
    session_code,
    sha256_bytes,
    sha256_json,
    validate_rating,
)
from gunnchos_device_os.cx4_validation_center.library import build_task_library
from gunnchos_device_os.cx4_validation_center.security import (
    assert_no_cloud_upload,
    assert_participant_cannot_forge_signoff,
    block_arbitrary_execution,
    media_allowed,
    require_strong_session_token,
    safe_join,
    sanitize_attachment_name,
)


class StoreError(Exception):
    def __init__(self, code: str, detail: str = ""):
        super().__init__(code)
        self.code = code
        self.detail = detail


class ValidationStore:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.sessions_dir = self.root / "sessions"
        self.submissions_dir = self.root / "submissions"
        self.evidence_dir = self.root / "evidence"
        self.autosave_dir = self.root / "autosave"
        for d in (self.sessions_dir, self.submissions_dir, self.evidence_dir, self.autosave_dir):
            d.mkdir(parents=True, exist_ok=True)
        self._submit_locks: Dict[str, str] = {}

    def _session_path(self, session_id: str) -> Path:
        return safe_join(self.sessions_dir, f"{session_id}.json")

    def save_session(self, session: Dict[str, Any]) -> Dict[str, Any]:
        assert_no_cloud_upload(session.get("privacy_state") or {})
        session = dict(session)
        session["updated_at"] = _now()
        path = self._session_path(session["session_id"])
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(session, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(path)
        auto = safe_join(self.autosave_dir, f"{session['session_id']}.json")
        auto.write_text(json.dumps(session, indent=2, sort_keys=True), encoding="utf-8")
        return session

    def load_session(self, session_id: str) -> Dict[str, Any]:
        path = self._session_path(session_id)
        if not path.is_file():
            auto = safe_join(self.autosave_dir, f"{session_id}.json")
            if auto.is_file():
                return json.loads(auto.read_text(encoding="utf-8"))
            raise StoreError("session_not_found", session_id)
        return json.loads(path.read_text(encoding="utf-8"))

    def list_sessions(self) -> List[Dict[str, Any]]:
        out = []
        for p in sorted(self.sessions_dir.glob("*.json")):
            try:
                out.append(json.loads(p.read_text(encoding="utf-8")))
            except Exception:
                continue
        return out

    def create_session(
        self,
        *,
        pack_ids: List[str],
        task_ids: List[str],
        participant_alias: str,
        moderator: str,
        device_sku: str = "",
        build_version: str = "",
        branch: str = "",
        commit: str = "",
        reviewer: str = "",
        lan_bind_opt_in: bool = False,
    ) -> Dict[str, Any]:
        if not participant_alias.strip():
            raise StoreError("participant_alias_required")
        if not pack_ids:
            raise StoreError("pack_ids_required")
        lib = {t.task_id: t for t in build_task_library()}
        if not task_ids:
            task_ids = [tid for tid, t in lib.items() if t.pack_id in pack_ids and t.active_by_default]
            if not task_ids:
                raise StoreError("task_ids_required_not_all_active_by_default")
        for tid in task_ids:
            if tid not in lib:
                raise StoreError("unknown_task", tid)
            if lib[tid].pack_id not in pack_ids:
                raise StoreError("task_not_in_selected_packs", tid)

        sid = new_id("sess")
        results = []
        for tid in task_ids:
            t = lib[tid]
            results.append(
                ValidationTaskResult(
                    task_id=tid,
                    step_completions=[False] * len(t.participant_steps),
                ).to_dict()
            )
        session = ValidationSession(
            session_id=sid,
            pack_ids=list(pack_ids),
            participant_alias=participant_alias.strip(),
            moderator=moderator.strip() or "moderator",
            reviewer=reviewer,
            device_sku=device_sku,
            build_version=build_version,
            branch=branch,
            commit=commit,
            started_at=None,
            task_results=results,
            session_status=SessionStatus.CONSENT_PENDING.value,
            session_code=session_code(),
            access_token=require_strong_session_token(),
            task_ids=list(task_ids),
            lan_bind_opt_in=bool(lan_bind_opt_in),
        ).to_dict()
        return self.save_session(session)

    def revoke_access(self, session_id: str) -> Dict[str, Any]:
        s = self.load_session(session_id)
        s["access_revoked"] = True
        s["access_token"] = require_strong_session_token()
        return self.save_session(s)

    def record_consent(self, session_id: str, consent: Dict[str, Any]) -> Dict[str, Any]:
        from gunnchos_device_os.cx4_validation_center.consent import normalize_consent

        s = self.load_session(session_id)
        normalized = normalize_consent(consent)
        s["consent_state"] = normalized
        if normalized.get("declined"):
            s["session_status"] = SessionStatus.REVOKED.value
        elif normalized.get("accepted"):
            s["session_status"] = SessionStatus.IN_PROGRESS.value
            s["started_at"] = s.get("started_at") or _now()
        return self.save_session(s)

    def patch_task_result(
        self,
        session_id: str,
        task_id: str,
        patch: Dict[str, Any],
        *,
        role: str = "participant",
    ) -> Dict[str, Any]:
        assert_participant_cannot_forge_signoff(role, patch)
        s = self.load_session(session_id)
        if s.get("session_status") == SessionStatus.SUBMITTED.value and role == "participant":
            raise StoreError("submitted_immutable_for_participant")
        found = False
        for tr in s["task_results"]:
            if tr["task_id"] == task_id:
                found = True
                if "participant_rating" in patch:
                    errs = validate_rating(patch["participant_rating"] or {})
                    if errs:
                        raise StoreError("invalid_rating", ",".join(errs))
                tr.update(patch)
                break
        if not found:
            raise StoreError("task_result_not_found", task_id)
        return self.save_session(s)

    def add_issue(self, session_id: str, issue: Dict[str, Any]) -> Dict[str, Any]:
        s = self.load_session(session_id)
        issue = dict(issue)
        issue.setdefault("issue_id", new_id("iss"))
        issue.setdefault("status", "open")
        for key in ("issue_id", "task_id", "severity", "category", "description"):
            if key not in issue:
                raise StoreError("issue_missing_field", key)
        s.setdefault("issues", []).append(issue)
        for tr in s["task_results"]:
            if tr["task_id"] == issue["task_id"]:
                tr.setdefault("issue_refs", []).append(issue["issue_id"])
        return self.save_session(s)

    def add_evidence_bytes(
        self,
        session_id: str,
        task_id: str,
        *,
        file_name: str,
        mime: str,
        data: bytes,
        source: str = EvidenceSource.HUMAN_OBSERVED.value,
        privacy_classification: str = "internal",
        attribution: str = "participant",
        notes: str = "",
        mock: bool = False,
    ) -> Dict[str, Any]:
        s = self.load_session(session_id)
        consent = s.get("consent_state") or {}
        if mime.startswith(("image/", "audio/", "video/")) and not media_allowed(consent, mime):
            raise StoreError("media_consent_required")
        clean = sanitize_attachment_name(file_name)
        block_arbitrary_execution(clean)
        eid = new_id("ev")
        digest = sha256_bytes(data)
        rel = f"{session_id}/{eid}_{clean}"
        dest = safe_join(self.evidence_dir, rel)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        item = EvidenceItem(
            evidence_id=eid,
            file_name=clean,
            mime=mime,
            sha256=digest,
            timestamp=_now(),
            source=source,
            task_id=task_id,
            privacy_classification=privacy_classification,
            attribution=attribution,
            relative_path=rel,
            notes=notes,
            mock=bool(mock),
        ).to_dict()
        s.setdefault("evidence", []).append(item)
        for tr in s["task_results"]:
            if tr["task_id"] == task_id:
                tr.setdefault("evidence_refs", []).append(eid)
        self.save_session(s)
        return item

    def submit_session(self, session_id: str, *, final_comments: str = "", force_incomplete: bool = False) -> Dict[str, Any]:
        s = self.load_session(session_id)
        if s.get("access_revoked"):
            raise StoreError("access_revoked")
        if not (s.get("consent_state") or {}).get("accepted"):
            raise StoreError("consent_required")
        if self._submit_locks.get(session_id) == "pending":
            raise StoreError("duplicate_submit_prevented")
        self._submit_locks[session_id] = "pending"
        try:
            incomplete = [
                tr["task_id"]
                for tr in s["task_results"]
                if tr.get("state") not in {"completed", "skipped"}
            ]
            if incomplete and not force_incomplete:
                s["session_status"] = SessionStatus.PENDING_SUBMISSION.value
                self.save_session(s)
                raise StoreError("incomplete_session", ",".join(incomplete))

            versions = sorted(
                p for p in self.submissions_dir.glob(f"{session_id}_v*.json") if "_session_snapshot" not in p.name
            )
            version = len(versions) + 1
            prev_hash = None
            if versions:
                prev = json.loads(versions[-1].read_text(encoding="utf-8"))
                prev_hash = prev.get("submission_hash")

            evidence_hashes = {e["evidence_id"]: e["sha256"] for e in s.get("evidence") or []}
            manifest = {
                "session_id": session_id,
                "pack_ids": s.get("pack_ids"),
                "task_ids": s.get("task_ids"),
                "participant_alias": s.get("participant_alias"),
                "device_sku": s.get("device_sku"),
                "build_version": s.get("build_version"),
                "incomplete_forced": bool(force_incomplete and incomplete),
                "incomplete_tasks": incomplete,
            }
            provenance = {
                "branch": s.get("branch"),
                "commit": s.get("commit"),
                "moderator": s.get("moderator"),
                "reviewer": s.get("reviewer"),
                "session_code": s.get("session_code"),
            }
            stamp = _now()
            body = {
                "manifest": manifest,
                "task_results": s.get("task_results"),
                "evidence_hashes": evidence_hashes,
                "issue_list": s.get("issues") or [],
                "provenance": provenance,
                "consent_state": s.get("consent_state"),
                "submission_timestamp": stamp,
                "version": version,
                "previous_submission_hash": prev_hash,
            }
            sub_hash = sha256_json(body)
            submission = ValidationSubmission(
                submission_id=new_id("sub"),
                session_id=session_id,
                version=version,
                manifest=manifest,
                task_results=list(s.get("task_results") or []),
                evidence_hashes=evidence_hashes,
                issue_list=list(s.get("issues") or []),
                provenance=provenance,
                consent_state=dict(s.get("consent_state") or {}),
                submission_timestamp=stamp,
                submission_hash=sub_hash,
                previous_submission_hash=prev_hash,
            ).to_dict()

            out_path = safe_join(self.submissions_dir, f"{session_id}_v{version}.json")
            if out_path.exists():
                raise StoreError("duplicate_submit_prevented")
            out_path.write_text(json.dumps(submission, indent=2, sort_keys=True), encoding="utf-8")
            s["final_comments"] = final_comments
            s["submitted_at"] = stamp
            s["session_status"] = SessionStatus.SUBMITTED.value
            s["latest_submission_id"] = submission["submission_id"]
            s["latest_submission_version"] = version
            s["latest_submission_hash"] = sub_hash
            self.save_session(s)
            snap = safe_join(self.submissions_dir, f"{session_id}_v{version}_session_snapshot.json")
            snap.write_text(json.dumps(s, indent=2, sort_keys=True), encoding="utf-8")
            return submission
        finally:
            self._submit_locks[session_id] = "done"

    def mutate_submission_in_place(self, session_id: str, version: int, patch: Dict[str, Any]) -> None:
        raise StoreError("submitted_snapshot_immutable")

    def load_submission(self, session_id: str, version: Optional[int] = None) -> Dict[str, Any]:
        if version is None:
            versions = sorted(
                p for p in self.submissions_dir.glob(f"{session_id}_v*.json") if "_session_snapshot" not in p.name
            )
            if not versions:
                raise StoreError("submission_not_found")
            path = versions[-1]
        else:
            path = safe_join(self.submissions_dir, f"{session_id}_v{version}.json")
        if not path.is_file():
            raise StoreError("submission_not_found")
        return json.loads(path.read_text(encoding="utf-8"))

    def reviewer_signoff(
        self,
        session_id: str,
        task_id: str,
        *,
        signoff: bool,
        notes: str = "",
        state: str = "signed_off",
        role: str = "reviewer",
    ) -> Dict[str, Any]:
        if role != "reviewer":
            raise StoreError("reviewer_role_required")
        s = self.load_session(session_id)
        if s.get("session_status") not in {
            SessionStatus.SUBMITTED.value,
            SessionStatus.NEEDS_CLARIFICATION.value,
            SessionStatus.REVIEWED.value,
        }:
            raise StoreError("session_not_submitted")
        patch = {
            "reviewer_signoff": bool(signoff),
            "reviewer_notes": notes,
            "reviewer_state": state if signoff else "clarification_requested",
        }
        s = self.patch_task_result(session_id, task_id, patch, role="reviewer")
        if all(tr.get("reviewer_signoff") for tr in s["task_results"]):
            s["session_status"] = SessionStatus.REVIEWED.value
            self.save_session(s)
        elif any(tr.get("reviewer_state") == "clarification_requested" for tr in s["task_results"]):
            s["session_status"] = SessionStatus.NEEDS_CLARIFICATION.value
            self.save_session(s)
        return s

    def recover_from_autosave(self, session_id: str) -> Dict[str, Any]:
        auto = safe_join(self.autosave_dir, f"{session_id}.json")
        if not auto.is_file():
            raise StoreError("autosave_missing")
        data = json.loads(auto.read_text(encoding="utf-8"))
        return self.save_session(data)
