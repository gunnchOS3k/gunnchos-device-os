"""Deep-link normalization and authorization for waike:// URIs."""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import unquote, unquote_to_bytes

DEEP_LINK_SCHEME = "waike"
ALLOWED_DEEP_LINK_KINDS = frozenset(
    {"learn", "section", "quiz", "assignment", "sync", "device"}
)
_KIND_RE = re.compile(r"^[a-z]+$", re.IGNORECASE)
_SAFE_SEGMENT_RE = re.compile(r"^[\w.\-]+$")


def _reject(uri: str, reason: str) -> dict[str, Any]:
    return {"uri": uri, "valid": False, "reason": reason, "kind": None, "path": None}


def _has_ambiguous_encoding(raw: str) -> bool:
    """Reject double-encoding and invalid percent sequences."""
    if "%" not in raw:
        return False
    i = 0
    while i < len(raw):
        if raw[i] != "%":
            i += 1
            continue
        if i + 2 >= len(raw):
            return True
        hexpart = raw[i + 1 : i + 3]
        if not re.fullmatch(r"[0-9A-Fa-f]{2}", hexpart):
            return True
        # Encoded percent that would yield another %XX after one decode → double encoding
        if hexpart.lower() == "25":
            return True
        i += 3
    return False


def _decode_once(segment: str) -> str | None:
    """Percent-decode once; return None on invalid/ambiguous encoding."""
    if _has_ambiguous_encoding(segment):
        return None
    try:
        raw_bytes = unquote_to_bytes(segment)
    except Exception:
        return None
    if b"\x00" in raw_bytes:
        return None
    try:
        decoded = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return None
    # Control characters (except common whitespace we still reject in paths)
    if any(ord(ch) < 32 for ch in decoded):
        return None
    return decoded


def parse_deep_link(uri: str | None) -> dict[str, Any]:
    """Parse and authorize a waike:// deep link with single percent-decode."""
    if not uri:
        return {"uri": None, "valid": True, "kind": None, "path": None, "reason": None}
    uri = uri.strip()
    if "\x00" in uri:
        return _reject(uri, "nul_rejected")
    if "\\" in uri:
        return _reject(uri, "backslash_rejected")
    lower = uri.lower()
    prefix = f"{DEEP_LINK_SCHEME}://"
    if not lower.startswith(prefix):
        return _reject(uri, "scheme_or_kind_rejected")

    rest = uri[len(prefix) :]
    if not rest:
        return _reject(uri, "scheme_or_kind_rejected")

    parts = rest.split("/")
    kind_raw = parts[0]
    kind_decoded = _decode_once(kind_raw)
    if kind_decoded is None:
        return _reject(uri, "encoding_rejected")
    kind = kind_decoded.lower()
    if not _KIND_RE.match(kind) or kind not in ALLOWED_DEEP_LINK_KINDS:
        return _reject(uri, "kind_rejected")

    path_segments: list[str] = []
    for seg in parts[1:]:
        if seg == "":
            continue
        decoded = _decode_once(seg)
        if decoded is None:
            return _reject(uri, "encoding_rejected")
        if "\\" in decoded or "/" in decoded:
            return _reject(uri, "path_traversal_rejected")
        if decoded in (".", "..") or ".." in decoded:
            return _reject(uri, "path_traversal_rejected")
        if not _SAFE_SEGMENT_RE.match(decoded):
            return _reject(uri, "path_segment_rejected")
        path_segments.append(decoded)

    path = "/".join(path_segments)
    canonical = f"{DEEP_LINK_SCHEME}://{kind}" + (f"/{path}" if path else "")
    return {
        "uri": uri,
        "canonical": canonical,
        "valid": True,
        "kind": kind,
        "path": path,
        "segments": path_segments,
        "reason": None,
    }
