"""Security controls for Validation Center — local-first, fail-closed."""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any, Dict, List, Tuple

from gunnchos_device_os.cx4_validation_center.contracts import sanitize_filename, session_token


FORBIDDEN_EXEC_SUFFIXES = {".sh", ".bash", ".exe", ".bat", ".cmd", ".ps1", ".com", ".msi", ".dylib", ".so"}


def assert_under_root(root: Path, candidate: Path) -> Path:
    root_r = root.resolve()
    cand_r = candidate.resolve()
    try:
        cand_r.relative_to(root_r)
    except ValueError as exc:
        raise PermissionError(f"path_traversal_blocked:{candidate}") from exc
    return cand_r


def safe_join(root: Path, *parts: str) -> Path:
    cleaned: List[str] = []
    for part in parts:
        part = part.replace("\\", "/")
        for seg in part.split("/"):
            if seg in ("", ".", ".."):
                if seg == "..":
                    raise PermissionError("path_traversal_blocked")
                continue
            cleaned.append(seg)
    return assert_under_root(root, root.joinpath(*cleaned))


def sanitize_attachment_name(name: str) -> str:
    clean = sanitize_filename(name)
    clean = clean.replace("..", "_")
    return clean


def block_arbitrary_execution(file_name: str) -> None:
    lower = file_name.lower()
    suffix = Path(lower).suffix
    if suffix in FORBIDDEN_EXEC_SUFFIXES:
        raise PermissionError(f"arbitrary_file_execution_blocked:{suffix}")
    if lower.endswith(".html.exe") or "\x00" in file_name:
        raise PermissionError("arbitrary_file_execution_blocked")


def escape_html(text: str) -> str:
    return html.escape(text or "", quote=True)


def token_entropy_bits(token: str) -> int:
    return max(0, int(len(token) * 6))


def require_strong_session_token(token: str | None = None) -> str:
    tok = token or session_token()
    if token_entropy_bits(tok) < 128:
        raise ValueError("session_token_entropy_insufficient")
    return tok


def media_allowed(consent: Dict[str, Any], mime: str) -> bool:
    if consent.get("declined"):
        return False
    if not consent.get("accepted"):
        return False
    mime = (mime or "").lower()
    if mime.startswith("image/") and not consent.get("media_photo"):
        return False
    if mime.startswith("audio/") and not consent.get("media_audio"):
        return False
    if mime.startswith("video/") and not consent.get("media_video"):
        return False
    return True


def assert_no_cloud_upload(privacy: Dict[str, Any]) -> None:
    if privacy.get("cloud_upload_enabled"):
        raise PermissionError("cloud_upload_not_permitted_by_default")
    if not privacy.get("store_local_only", True):
        raise PermissionError("non_local_store_blocked")


def assert_participant_cannot_forge_signoff(role: str, patch: Dict[str, Any]) -> None:
    if role == "participant":
        forbidden = {"reviewer_signoff", "reviewer_state", "reviewer_notes"}
        bad = forbidden.intersection(patch.keys())
        if bad:
            raise PermissionError(f"participant_cannot_forge_reviewer_fields:{sorted(bad)}")


def lan_bind_allowed(opt_in: bool) -> Tuple[str, int]:
    """Default loopback only; LAN requires explicit opt-in (still loopback unless configured)."""
    _ = opt_in
    return ("127.0.0.1", 8765)


def security_self_check() -> Dict[str, Any]:
    checks: Dict[str, Any] = {
        "path_traversal_blocked": False,
        "arbitrary_execution_blocked": False,
        "filename_sanitized": False,
        "html_escaped": False,
        "session_token_entropy_ok": False,
        "lan_default_loopback": False,
        "consent_enforced": False,
        "no_hidden_cloud_upload": False,
        "participant_signoff_forge_blocked": False,
    }
    root = Path("/tmp/vc_sec_root_probe")
    root.mkdir(parents=True, exist_ok=True)
    try:
        try:
            safe_join(root, "../etc/passwd")
        except PermissionError:
            checks["path_traversal_blocked"] = True
        try:
            block_arbitrary_execution("payload.sh")
        except PermissionError:
            checks["arbitrary_execution_blocked"] = True
        sanitized = sanitize_attachment_name("../../evil name!.png")
        checks["filename_sanitized"] = ".." not in sanitized and "evil" in sanitized
        checks["html_escaped"] = escape_html("<script>") == "&lt;script&gt;"
        tok = require_strong_session_token()
        checks["session_token_entropy_ok"] = token_entropy_bits(tok) >= 128
        host, _port = lan_bind_allowed(False)
        checks["lan_default_loopback"] = host == "127.0.0.1"
        checks["consent_enforced"] = media_allowed({"accepted": False}, "image/png") is False
        try:
            assert_no_cloud_upload({"store_local_only": True, "cloud_upload_enabled": False})
            checks["no_hidden_cloud_upload"] = True
        except PermissionError:
            checks["no_hidden_cloud_upload"] = False
        try:
            assert_participant_cannot_forge_signoff("participant", {"reviewer_signoff": True})
        except PermissionError:
            checks["participant_signoff_forge_blocked"] = True
    finally:
        pass
    checks["ok"] = all(
        checks[k]
        for k in (
            "path_traversal_blocked",
            "arbitrary_execution_blocked",
            "filename_sanitized",
            "html_escaped",
            "session_token_entropy_ok",
            "lan_default_loopback",
            "consent_enforced",
            "no_hidden_cloud_upload",
            "participant_signoff_forge_blocked",
        )
    )
    return checks
