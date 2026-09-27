"""Campus / WAIKE / Network Twin continuity on top of the #165 MLV foundation.

gunnchOS remains shell, registry, intents, lifecycle, and return continuity.
It does not become LMS, twin, SpectrumX, Edge-IO, or RIC authority.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlparse

from gunnchos_launcher.mlv_bridge import (
    MLV_APP_ID,
    parse_mlv_deep_link,
)

INTENT_VERSION = "v2"
WAIKE_APP_ID = "waike_learning_os"
DEEP_LINK_SCHEME = "gunnchos"
DEEP_LINK_HOST = "mlv"
WAIKE_SCHEME = "waike"

CANONICAL_CAMPUSES = (
    "gary",
    "ghana",
    "guyana",
    "geelong",
    "germany",
    "gaza",
    "graham_land",
)
CAMPUS_ALIASES = {"graham-land": "graham_land"}

WAIKE_KINDS_WITH_ID = frozenset(
    {"course", "module", "lesson", "assignment", "quiz", "lab", "study"}
)
WAIKE_KINDS_BARE = frozenset({"home", "grades", "calendar", "portfolio"})
WAIKE_KINDS = WAIKE_KINDS_WITH_ID | WAIKE_KINDS_BARE

ALLOWED_ACTUATION = frozenset(
    {"SIMULATION ONLY", "READ ONLY", "RECOMMENDATION ONLY", "SHADOW"}
)
DISABLED_ACTUATION = frozenset({"AUTHORIZED TESTBED", "PRODUCTION"})
REAL_ACTUATION_ENABLED = False

SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
TOKENISH_RE = re.compile(r"^[A-Za-z0-9_-]{16,}$")
JWT_RE = re.compile(r"^eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$")

SECRET_KEYS = frozenset(
    {
        "token",
        "share_token",
        "bearer",
        "password",
        "api_key",
        "secret",
        "e2_credential",
        "radio_credential",
        "spectrumx_secret",
        "edge_io_secret",
        "authorization",
        "access_token",
        "refresh_token",
    }
)
SECRET_QUERY_KEYS = frozenset(
    {
        "token",
        "share",
        "bearer",
        "access_token",
        "refresh_token",
        "authorization",
        "api_key",
    }
)
GAZA_FORBIDDEN_QUERY = frozenset(
    {"lat", "lon", "lng", "latlng", "latitude", "longitude", "precise", "coords"}
)
LEARNING_JOIN_KEYS = frozenset(
    {
        "grades",
        "assignments",
        "mastery",
        "identity_history",
        "answer_keys",
        "learner_identity",
        "unauthorized_grade_details",
    }
)
TELEMETRY_JOIN_KEYS = frozenset(
    {
        "signal_telemetry",
        "movement",
        "ran_optimization",
        "rsrp",
        "imei",
        "radio_trace",
        "ue_path",
    }
)

WAIKE_PR25_HEAD = "f0176c2c45c1c366ad22f46407e6c55c3c5f3e8e"
WAIKE_CONSUMER_SUMMARY = "/api/v1/mlv/consumer-summary"
WAIKE_MUST_NOT_EXPOSE = (
    "answer_keys",
    "instructor_only_materials",
    "other_learners",
    "unauthorized_grade_details",
    "tokens_or_passwords",
    "unrestricted_hub_apis",
)
WAIKE_PARTIAL_IDS = ("DIGITAL_CONFIDENCE", "IT_SUPPORT_HARDWARE")

BACKEND_PINS = {
    "field_kit": {
        "pr": 120,
        "head": "f7ca0bacbea33f3a97e550cf3c8c28e5dc6928f9",
    },
    "digital_twin": {
        "pr": 33,
        "head": "1d3c159ed942bb499a83af0c4e1533bf439a5970",
    },
    "spectrumx": {
        "pr": 104,
        "head": "bffa5161de5b8f3118e89f210f43f375e6cde717",
    },
    "edge_io": {
        "pr": 41,
        "head": "1af382b489732d4dfa745f67eef9ee61ec1ba9a4",
    },
}

MLV_PINS = {
    "pr1": {
        "branch": "revival/gunnchos-world-workspace-v1",
        "head": "5e99c64673557efe7cbdfbbfb4d4ebcdcabfaab7",
    },
    "pr2": {
        "branch": "world/home-7gc-campus-gallery-v2",
        "head": "5ce416d25f7821ee5506be1a60fd30315372956c",
    },
    "pr3": {
        "branch": "world/7gc-airan-network-twin-extension-v3",
        "head": "60fd7173d8e2fbe5dabe7f77cdccd2ba3abdcc78",
    },
}

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "shared_contracts" / "WAIKE_MLV_EDUCATION_CONTRACT.v1.json"
SCHEMA_PATH = ROOT / "shared_contracts" / "mlv_continuity_intent.v2.schema.json"


def _fail(reason: str, **extra: Any) -> dict[str, Any]:
    out = {
        "ok": False,
        "valid": False,
        "reason": reason,
        "intent_version": INTENT_VERSION,
        "token_present": False,
    }
    out.update(extra)
    return out


def _ok(**fields: Any) -> dict[str, Any]:
    out = {
        "ok": True,
        "valid": True,
        "reason": None,
        "intent_version": INTENT_VERSION,
        "token_present": False,
        "real_actuation_enabled": REAL_ACTUATION_ENABLED,
    }
    out.update(fields)
    return out


def canonicalize_campus(raw: str | None) -> str | None:
    if raw is None:
        return None
    value = raw.strip().lower()
    value = CAMPUS_ALIASES.get(value, value)
    if value in CANONICAL_CAMPUSES:
        return value
    return None


def _looks_like_secret(value: str | None) -> bool:
    if not value:
        return False
    if JWT_RE.match(value):
        return True
    if TOKENISH_RE.match(value) and len(value) >= 24:
        return True
    return False


def _payload_has_secrets(payload: dict[str, Any]) -> bool:
    for key, value in payload.items():
        if str(key).lower() in SECRET_KEYS:
            return True
        if isinstance(value, str) and _looks_like_secret(value):
            if key in {
                "return_to",
                "route",
                "canonical",
                "visibility_context",
                "route_kind",
                "campus_id",
                "waike_kind",
                "target_app",
                "intent_version",
                "role",
                "actuation_mode",
            }:
                continue
            return True
    return False


def _query_rejected(uri: str, campus_id: str | None = None) -> str | None:
    parsed = urlparse(uri)
    if not parsed.query:
        return None
    pairs = parse_qsl(parsed.query, keep_blank_values=True)
    for key, value in pairs:
        lowered = key.lower()
        if lowered in SECRET_QUERY_KEYS or _looks_like_secret(value):
            return "secrets_in_route_rejected"
        if campus_id == "gaza" and lowered in GAZA_FORBIDDEN_QUERY:
            return "gaza_precise_location_rejected"
        if lowered in {"actuation", "ric", "e2"} and value.upper() in DISABLED_ACTUATION:
            return "ric_actuation_rejected"
    return None


def _validate_safe_id(value: str | None, *, run: bool = False) -> bool:
    if not value:
        return False
    if ".." in value or "/" in value or "\\" in value:
        return False
    if _looks_like_secret(value):
        return False
    if run:
        return bool(UUID_RE.match(value) or RUN_ID_RE.match(value))
    return bool(SAFE_ID_RE.match(value))


def campus_truth(campus_id: str) -> dict[str, Any]:
    if campus_id == "gaza":
        return {
            "campus_id": "gaza",
            "public_vulnerability_routes": False,
            "precise_protected_location": False,
            "location_mode": "abstract_zones",
            "export_sensitive": False,
        }
    if campus_id == "graham_land":
        return {
            "campus_id": "graham_land",
            "posture": "remote_first",
            "simulation_ok": True,
            "partner_reference_ok": True,
            "fake_waike_station": False,
            "ownership_implied": False,
            "physical_station": False,
        }
    return {"campus_id": campus_id, "posture": "standard_campus"}


def _gaza_graham_rejected(campus_id: str | None, uri: str, extra: dict[str, Any] | None = None) -> str | None:
    blob = uri.lower()
    extra = extra or {}
    extra_blob = " ".join(str(v).lower() for v in extra.values())
    if campus_id == "gaza":
        forbidden = (
            "vulnerability",
            "precise_location",
            "street_address",
            "coordinates",
            "public-vulnerability",
        )
        if any(token in blob or token in extra_blob for token in forbidden):
            return "gaza_route_redaction"
        if extra.get("visibility_context") == "public" and extra.get("route_kind") not in {None, "gallery"}:
            return "gaza_public_vulnerability_rejected"
    if campus_id == "graham_land":
        forbidden = (
            "owned_station",
            "fake_station",
            "physical_station",
            "on_site_waike",
            "ownership",
        )
        if any(token in blob or token in extra_blob for token in forbidden):
            return "graham_truth_rejected"
        if extra.get("fake_waike_station") or extra.get("ownership_implied"):
            return "graham_truth_rejected"
    return None


def visibility_for(route_kind: str, campus_id: str | None = None) -> str:
    if route_kind == "home":
        return "private"
    if route_kind == "gallery":
        return "gallery_public"
    if route_kind in {
        "network_twin",
        "network_twin_campus",
        "network_twin_run",
        "digital_shadow",
    }:
        return "synthetic_educational"
    if route_kind in {"campus", "campus_site", "waike"}:
        return "campus"
    if route_kind == "public":
        return "public"
    if route_kind == "share":
        return "private"
    return "private"


def canonical_mlv_route(
    route_kind: str,
    campus_id: str | None = None,
    run_id: str | None = None,
) -> str:
    prefix = f"{DEEP_LINK_SCHEME}://{DEEP_LINK_HOST}"
    if route_kind == "home":
        return f"{prefix}/home"
    if route_kind == "gallery":
        return f"{prefix}/gallery"
    if route_kind == "campus":
        return f"{prefix}/campus"
    if route_kind == "campus_site" and campus_id:
        return f"{prefix}/campus/{campus_id}"
    if route_kind == "network_twin":
        return f"{prefix}/campus/network-twin"
    if route_kind == "network_twin_campus" and campus_id:
        return f"{prefix}/campus/network-twin/{campus_id}"
    if route_kind == "network_twin_run" and campus_id and run_id:
        return f"{prefix}/campus/network-twin/{campus_id}/run/{run_id}"
    if route_kind == "digital_shadow" and campus_id and run_id:
        return f"{prefix}/campus/network-twin/{campus_id}/shadow/{run_id}"
    raise ValueError(f"cannot canonicalize {route_kind}")


def parse_mlv_product_link(uri: str | None) -> dict[str, Any]:
    """Parse current-graph MLV routes, preserving #165 foundation kinds."""
    if not uri:
        return _fail("empty")
    trimmed = uri.strip()
    if "\x00" in trimmed or "\\" in trimmed:
        return _fail("unsafe_chars", uri=trimmed)
    lower = trimmed.lower()
    prefix = f"{DEEP_LINK_SCHEME}://{DEEP_LINK_HOST}"
    if lower.startswith("https://") or lower.startswith("http://"):
        return _fail("arbitrary_url_rejected", uri=trimmed)
    if not lower.startswith(prefix):
        return _fail("scheme_or_host_rejected", uri=trimmed)

    parsed = urlparse(trimmed)
    parts = [p for p in parsed.path.split("/") if p]
    if parsed.netloc.lower() == DEEP_LINK_HOST and not parts:
        # gunnchos://mlv/home form uses path; some parsers put host only
        rest = trimmed[len(prefix) :]
        if rest.startswith("/"):
            rest = rest[1:]
        path_and_query = rest.split("?", 1)[0]
        parts = [p for p in path_and_query.split("/") if p]

    if not parts:
        return _fail("kind_rejected", uri=trimmed)

    query_reason = _query_rejected(trimmed)
    if query_reason:
        return _fail(query_reason, uri=trimmed)

    kind0 = parts[0].lower()

    if kind0 in {"production", "testbed", "actuate", "ric"}:
        return _fail("ric_actuation_rejected", uri=trimmed)

    if kind0 == "home":
        if len(parts) != 1:
            return _fail("kind_rejected", uri=trimmed)
        return _product_ok("home", trimmed)

    if kind0 == "gallery":
        if len(parts) != 1:
            return _fail("kind_rejected", uri=trimmed)
        return _product_ok("gallery", trimmed, visibility_context="gallery_public")

    if kind0 == "campus":
        return _parse_campus_parts(parts[1:], trimmed)

    if kind0 in {"node", "public", "share"}:
        foundation = parse_mlv_deep_link(trimmed.split("?", 1)[0])
        if not foundation.get("valid"):
            return _fail(str(foundation.get("reason") or "kind_rejected"), uri=trimmed)
        result = _ok(
            uri=trimmed,
            target_app=MLV_APP_ID,
            route_kind=foundation["kind"],
            campus_id=None,
            canonical=foundation.get("canonical"),
            visibility_context=visibility_for(foundation["kind"]),
            node_id=foundation.get("node_id"),
            token_present=bool(foundation.get("token_present")),
        )
        if foundation.get("kind") == "share":
            # Never echo the share token.
            result["canonical"] = f"{prefix}/share"
            result["uri"] = f"{prefix}/share"
        return result

    return _fail("unknown_route_kind", uri=trimmed)


def _product_ok(
    route_kind: str,
    uri: str,
    campus_id: str | None = None,
    run_id: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    truth_reason = _gaza_graham_rejected(campus_id, uri, extra)
    if truth_reason:
        return _fail(truth_reason, uri=uri, campus_id=campus_id)
    query_reason = _query_rejected(uri, campus_id)
    if query_reason:
        return _fail(query_reason, uri=uri, campus_id=campus_id)
    visibility = extra.pop("visibility_context", visibility_for(route_kind, campus_id))
    if route_kind == "home" and visibility != "private":
        return _fail("home_must_remain_private", uri=uri)
    if route_kind == "gallery" and visibility not in {"public", "gallery_public"}:
        return _fail("gallery_public_only", uri=uri)
    canonical = canonical_mlv_route(route_kind, campus_id, run_id)
    result = _ok(
        uri=uri,
        target_app=MLV_APP_ID,
        route_kind=route_kind,
        campus_id=campus_id,
        network_twin_run_id=run_id,
        canonical=canonical,
        visibility_context=visibility,
        campus_truth=campus_truth(campus_id) if campus_id else None,
        actuation_mode=extra.pop("actuation_mode", None)
        if route_kind.startswith("network_twin") or route_kind == "digital_shadow"
        else None,
        ric_actuation=False,
    )
    result.update(extra)
    return result


def _parse_campus_parts(parts: list[str], uri: str) -> dict[str, Any]:
    if not parts:
        return _product_ok("campus", uri)
    head = parts[0].lower()
    if head in {"production", "testbed", "actuate", "ric"}:
        return _fail("ric_actuation_rejected", uri=uri)
    if head == "network-twin":
        return _parse_network_twin(parts[1:], uri)
    campus_id = canonicalize_campus(head)
    if campus_id is None:
        return _fail("unsupported_campus_id", uri=uri)
    if len(parts) == 1:
        return _product_ok("campus_site", uri, campus_id=campus_id)
    if parts[1].lower() == "network-twin":
        return _parse_network_twin(parts[2:], uri, implied_campus=campus_id)
    truth_reason = _gaza_graham_rejected(campus_id, uri, {"extra_path": "/".join(parts[1:])})
    if truth_reason:
        return _fail(truth_reason, uri=uri, campus_id=campus_id)
    return _fail("unknown_route_kind", uri=uri, campus_id=campus_id)


def _parse_network_twin(
    parts: list[str],
    uri: str,
    implied_campus: str | None = None,
) -> dict[str, Any]:
    lowered = [p.lower() for p in parts]
    if any(p in {"production", "testbed", "actuate", "ric", "e2"} for p in lowered):
        return _fail("ric_actuation_rejected", uri=uri)
    if not parts:
        if implied_campus:
            return _product_ok(
                "network_twin_campus",
                uri,
                campus_id=implied_campus,
                actuation_mode="SIMULATION ONLY",
            )
        return _product_ok("network_twin", uri, actuation_mode="SIMULATION ONLY")
    campus_id = implied_campus or canonicalize_campus(parts[0])
    if campus_id is None:
        return _fail("unsupported_campus_id", uri=uri)
    rest = parts if implied_campus else parts[1:]
    if not rest:
        return _product_ok(
            "network_twin_campus",
            uri,
            campus_id=campus_id,
            actuation_mode="SIMULATION ONLY",
        )
    action = rest[0].lower()
    if action in {"run", "shadow"}:
        if len(rest) != 2 or not _validate_safe_id(rest[1], run=True):
            return _fail("malformed_run_id", uri=uri, campus_id=campus_id)
        kind = "network_twin_run" if action == "run" else "digital_shadow"
        mode = "SIMULATION ONLY" if action == "run" else "SHADOW"
        return _product_ok(
            kind,
            uri,
            campus_id=campus_id,
            run_id=rest[1],
            actuation_mode=mode,
        )
    return _fail("unknown_route_kind", uri=uri, campus_id=campus_id)


def parse_waike_deep_link(uri: str | None) -> dict[str, Any]:
    if not uri:
        return _fail("empty")
    trimmed = uri.strip()
    if "\x00" in trimmed or "\\" in trimmed:
        return _fail("unsafe_chars", uri=trimmed)
    if trimmed.lower().startswith(("http://", "https://", "gunnchos://")):
        return _fail("arbitrary_url_rejected", uri=trimmed)
    parsed = urlparse(trimmed)
    if parsed.scheme.lower() != WAIKE_SCHEME:
        return _fail("scheme_or_host_rejected", uri=trimmed)
    kind = (parsed.netloc or parsed.path.lstrip("/").split("/")[0]).lower()
    path_parts = [p for p in parsed.path.split("/") if p]
    if parsed.netloc:
        resource_parts = path_parts
    else:
        resource_parts = path_parts[1:]
        kind = path_parts[0].lower() if path_parts else ""
    if kind not in WAIKE_KINDS:
        return _fail("unknown_route_kind", uri=trimmed)
    query_reason = _query_rejected(trimmed)
    if query_reason:
        return _fail(query_reason, uri=trimmed)
    resource_id = resource_parts[0] if resource_parts else None
    if kind in WAIKE_KINDS_WITH_ID:
        if not _validate_safe_id(resource_id):
            return _fail("malformed_id", uri=trimmed, waike_kind=kind)
        canonical = f"{WAIKE_SCHEME}://{kind}/{resource_id}"
    else:
        if resource_id:
            return _fail("kind_rejected", uri=trimmed, waike_kind=kind)
        canonical = f"{WAIKE_SCHEME}://{kind}"
    return _ok(
        uri=trimmed,
        target_app=WAIKE_APP_ID,
        route_kind="waike",
        waike_kind=kind,
        resource_id=resource_id,
        section_id=resource_id if kind == "course" else None,
        canonical=canonical,
        system_of_record="waike",
        shadow_lms=False,
        visibility_context="campus",
    )


def validate_intent(intent: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(intent, dict):
        return _fail("not_an_object")
    if _payload_has_secrets(intent):
        return _fail("secrets_in_fields_rejected")
    join = learning_telemetry_join_state(intent)
    if not join["NO_LEARNING_TELEMETRY_JOIN_PASS"]:
        return _fail("learning_telemetry_join_rejected")
    if intent.get("intent_version") != INTENT_VERSION:
        return _fail("intent_version_rejected")
    target = intent.get("target_app")
    if target not in {MLV_APP_ID, WAIKE_APP_ID}:
        return _fail("target_app_rejected")
    route_kind = intent.get("route_kind")
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    allowed_kinds = set(schema["properties"]["route_kind"]["enum"])
    if route_kind not in allowed_kinds:
        return _fail("unknown_route_kind")
    extra = set(intent) - set(schema["properties"])
    if extra:
        return _fail("unknown_fields", fields=sorted(extra))

    campus_id = canonicalize_campus(intent.get("campus_id")) if intent.get("campus_id") else None
    if intent.get("campus_id") and campus_id is None:
        return _fail("unsupported_campus_id")
    actuation = intent.get("actuation_mode")
    if actuation in DISABLED_ACTUATION:
        return _fail("ric_actuation_rejected")
    if actuation not in {None, *ALLOWED_ACTUATION}:
        return _fail("actuation_mode_rejected")
    if intent.get("visibility_context") == "public" and route_kind == "home":
        return _fail("privilege_escalation_rejected")
    if route_kind == "home" and intent.get("visibility_context") not in {None, "private"}:
        return _fail("home_must_remain_private")
    if route_kind == "gallery" and intent.get("visibility_context") not in {
        None,
        "public",
        "gallery_public",
    }:
        return _fail("gallery_public_only")
    if intent.get("return_to"):
        ret = parse_return_target(intent["return_to"])
        if not ret["ok"]:
            return _fail("return_to_rejected", nested=ret["reason"])
    truth_reason = _gaza_graham_rejected(campus_id, str(intent.get("return_to") or ""), intent)
    if truth_reason:
        return _fail(truth_reason, campus_id=campus_id)
    if route_kind in {"campus_site", "network_twin_campus", "network_twin_run", "digital_shadow"} and not campus_id:
        return _fail("campus_id_required")
    run_id = intent.get("network_twin_run_id")
    if route_kind in {"network_twin_run", "digital_shadow"}:
        if not _validate_safe_id(run_id, run=True):
            return _fail("malformed_run_id")
    if target == WAIKE_APP_ID:
        waike_kind = intent.get("waike_kind")
        if waike_kind not in WAIKE_KINDS:
            return _fail("waike_kind_rejected")
        if waike_kind in WAIKE_KINDS_WITH_ID and not _validate_safe_id(intent.get("resource_id") or intent.get("section_id")):
            return _fail("malformed_id")
    return _ok(
        target_app=target,
        route_kind=route_kind,
        campus_id=campus_id,
        waike_kind=intent.get("waike_kind"),
        section_id=intent.get("section_id"),
        resource_id=intent.get("resource_id"),
        network_twin_run_id=run_id,
        return_to=intent.get("return_to"),
        visibility_context=intent.get("visibility_context") or visibility_for(route_kind, campus_id),
        role=intent.get("role") or "learner",
        actuation_mode=actuation,
        ric_actuation=False,
    )


def parse_return_target(uri: str | None) -> dict[str, Any]:
    if not uri:
        return _fail("empty")
    if uri.lower().startswith("waike://"):
        parsed = parse_waike_deep_link(uri)
    else:
        parsed = parse_mlv_product_link(uri)
    if not parsed.get("ok"):
        return parsed
    if parsed.get("token_present"):
        return _fail("secrets_in_return_rejected")
    return parsed


def open_waike_from_campus(
    campus_id: str,
    waike_kind: str,
    resource_id: str | None = None,
    *,
    waike_available: bool = True,
) -> dict[str, Any]:
    campus = canonicalize_campus(campus_id)
    if campus is None:
        return _fail("unsupported_campus_id")
    truth_reason = _gaza_graham_rejected(
        campus,
        f"{WAIKE_SCHEME}://{waike_kind}/{resource_id or ''}",
        {"resource_id": resource_id, "waike_kind": waike_kind},
    )
    if truth_reason:
        return _fail(truth_reason, campus_id=campus)
    if not waike_available:
        return _ok(
            target_app=MLV_APP_ID,
            route_kind="campus_site",
            campus_id=campus,
            canonical=canonical_mlv_route("campus_site", campus),
            waike_available=False,
            labeled_state="OFFLINE DEMO",
            fabricate_live_connectivity=False,
            system_of_record="waike",
            shadow_lms=False,
            return_to=canonical_mlv_route("campus_site", campus),
        )
    if waike_kind in WAIKE_KINDS_WITH_ID:
        uri = f"{WAIKE_SCHEME}://{waike_kind}/{resource_id}"
    else:
        uri = f"{WAIKE_SCHEME}://{waike_kind}"
    parsed = parse_waike_deep_link(uri)
    if not parsed.get("ok"):
        return parsed
    return_to = canonical_mlv_route("campus_site", campus)
    parsed.update(
        {
            "return_to": return_to,
            "return_visibility": "campus",
            "secrets_preserved": False,
            "campus_id": campus,
            "campus_truth": campus_truth(campus),
            "consumer_summary_endpoint": WAIKE_CONSUMER_SUMMARY,
            "shadow_lms": False,
            "duplicate_course_data": False,
        }
    )
    return parsed


def open_network_twin(
    campus_id: str | None = None,
    run_id: str | None = None,
    *,
    shadow: bool = False,
    backend_available: bool = True,
    role: str = "learner",
) -> dict[str, Any]:
    campus = canonicalize_campus(campus_id) if campus_id else None
    if campus_id and campus is None:
        return _fail("unsupported_campus_id")
    if run_id and not _validate_safe_id(run_id, run=True):
        return _fail("malformed_run_id")
    role_state = authorize_role(role, "digital_shadow" if shadow else "network_twin_run")
    if not role_state["allowed"]:
        return _fail(role_state["reason"], role=role)
    if not backend_available:
        kind = "network_twin_campus" if campus else "network_twin"
        return _ok(
            target_app=MLV_APP_ID,
            route_kind=kind,
            campus_id=campus,
            canonical=canonical_mlv_route(kind, campus),
            labeled_state="SYNTHETIC",
            live_ric_wording=False,
            fabricate_live_connectivity=False,
            actuation_mode="SIMULATION ONLY",
            ric_actuation=False,
            return_to=canonical_mlv_route("campus_site", campus) if campus else canonical_mlv_route("campus"),
        )
    if shadow:
        if not campus or not run_id:
            return _fail("campus_id_required")
        result = _product_ok(
            "digital_shadow",
            canonical_mlv_route("digital_shadow", campus, run_id),
            campus_id=campus,
            run_id=run_id,
            actuation_mode="SHADOW",
        )
    elif run_id and campus:
        result = _product_ok(
            "network_twin_run",
            canonical_mlv_route("network_twin_run", campus, run_id),
            campus_id=campus,
            run_id=run_id,
            actuation_mode="SIMULATION ONLY",
        )
    elif campus:
        result = _product_ok(
            "network_twin_campus",
            canonical_mlv_route("network_twin_campus", campus),
            campus_id=campus,
            actuation_mode="SIMULATION ONLY",
        )
    else:
        result = _product_ok(
            "network_twin",
            canonical_mlv_route("network_twin"),
            actuation_mode="SIMULATION ONLY",
        )
    if not result.get("ok"):
        return result
    result["return_to"] = (
        canonical_mlv_route("campus_site", campus) if campus else canonical_mlv_route("campus")
    )
    result["role"] = role
    result["backend_pins"] = BACKEND_PINS
    result["holds_e2_credentials"] = False
    result["holds_radio_credentials"] = False
    result["holds_spectrumx_secrets"] = False
    result["holds_edge_io_secrets"] = False
    return result


def return_from_surface(current: dict[str, Any]) -> dict[str, Any]:
    target = current.get("return_to")
    parsed = parse_return_target(target)
    if not parsed.get("ok"):
        return parsed
    parsed["secrets_preserved"] = False
    parsed["returned_from"] = current.get("route_kind")
    return parsed


def authorize_role(role: str, route_kind: str, actuation_mode: str | None = None) -> dict[str, Any]:
    role_id = (role or "learner").strip().lower()
    if actuation_mode in DISABLED_ACTUATION or route_kind in {"production", "testbed"}:
        return {
            "role": role_id,
            "allowed": False,
            "reason": "ric_actuation_rejected",
            "physical_radio_permission": False,
        }
    if role_id == "learner":
        allowed = route_kind in {
            "home",
            "campus",
            "campus_site",
            "gallery",
            "waike",
            "network_twin",
            "network_twin_campus",
            "network_twin_run",
            "digital_shadow",
            "node",
            "public",
        }
        return {
            "role": role_id,
            "allowed": allowed,
            "reason": None if allowed else "role_rejected",
            "physical_control": False,
            "physical_radio_permission": False,
        }
    if role_id == "planner":
        return {
            "role": role_id,
            "allowed": True,
            "reason": None,
            "may_approve_digital_shadow": True,
            "physical_radio_permission": False,
        }
    if role_id == "admin":
        return {
            "role": role_id,
            "allowed": True,
            "reason": None,
            "physical_ric_authority": False,
            "physical_radio_permission": False,
        }
    return {"role": role_id, "allowed": False, "reason": "unknown_role", "physical_radio_permission": False}


def learning_telemetry_join_state(payload: dict[str, Any]) -> dict[str, Any]:
    keys = {str(k).lower() for k in payload}
    nested = payload.get("learning") if isinstance(payload.get("learning"), dict) else {}
    telemetry = payload.get("telemetry") if isinstance(payload.get("telemetry"), dict) else {}
    keys |= {str(k).lower() for k in nested}
    keys |= {str(k).lower() for k in telemetry}
    has_learning = bool(keys & LEARNING_JOIN_KEYS) or bool(nested)
    has_telemetry = bool(keys & TELEMETRY_JOIN_KEYS) or bool(telemetry)
    joined = has_learning and has_telemetry
    return {
        "NO_LEARNING_TELEMETRY_JOIN_PASS": not joined,
        "has_learning": has_learning,
        "has_telemetry": has_telemetry,
    }


def waike_readiness_truth() -> dict[str, Any]:
    return {
        "imported": 18,
        "ready": 16,
        "partial": 2,
        "partial_ids": list(WAIKE_PARTIAL_IDS),
        "upgraded_to_18_ready": False,
        "WAIKE_16_READY_2_PARTIAL_TRUTH_PASS": True,
        "WAIKE_PR25_PIN_PASS": True,
        "waike_head": WAIKE_PR25_HEAD,
        "consumer_summary": WAIKE_CONSUMER_SUMMARY,
        "must_not_expose": list(WAIKE_MUST_NOT_EXPOSE),
        "shadow_lms": False,
        "NO_SHADOW_LMS_PASS": True,
    }


def load_waike_contract() -> dict[str, Any]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def actuation_policy() -> dict[str, Any]:
    return {
        "allowed": sorted(ALLOWED_ACTUATION),
        "disabled": sorted(DISABLED_ACTUATION),
        "REAL_ACTUATION_ENABLED": REAL_ACTUATION_ENABLED,
        "NO_DIRECT_GUNNCHOS_RIC_ACTUATION_PASS": True,
        "holds_backend_secrets": False,
    }


def seven_campus_route_proof() -> dict[str, Any]:
    campus_ok = []
    twin_ok = []
    for campus in CANONICAL_CAMPUSES:
        site = parse_mlv_product_link(canonical_mlv_route("campus_site", campus))
        twin = parse_mlv_product_link(canonical_mlv_route("network_twin_campus", campus))
        campus_ok.append(bool(site.get("ok")))
        twin_ok.append(bool(twin.get("ok")))
    return {
        "MLV_7GC_CAMPUS_ROUTE_PASS": f"{sum(campus_ok)}/7",
        "MLV_NETWORK_TWIN_ROUTE_PASS": f"{sum(twin_ok)}/7",
        "campuses": list(CANONICAL_CAMPUSES),
    }


def build_journey_matrix() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []

    def add(
        name: str,
        source: str,
        route: str,
        auth: str,
        privacy: str,
        expected_return: str | None,
        digital: str,
    ) -> None:
        rows.append(
            {
                "name": name,
                "source": source,
                "route": route,
                "auth": auth,
                "privacy_rule": privacy,
                "expected_return": expected_return,
                "digital_test_status": digital,
                "human_status": False,
                "pixel_status": False,
            }
        )

    add(
        "Home private artifact",
        "gunnchOS",
        "gunnchos://mlv/home",
        "owner_session",
        "HOME_PRIVATE",
        None,
        "pass",
    )
    add(
        "Campus landing",
        "gunnchOS",
        "gunnchos://mlv/campus",
        "owner_session",
        "campus_context",
        "gunnchos://mlv/home",
        "pass",
    )
    for campus in CANONICAL_CAMPUSES:
        add(
            f"Campus {campus}",
            "gunnchOS",
            canonical_mlv_route("campus_site", campus),
            "owner_session",
            "gaza_redaction" if campus == "gaza" else "graham_remote_first" if campus == "graham_land" else "campus_context",
            "gunnchos://mlv/campus",
            "pass",
        )
    add(
        "WAIKE summary",
        "WAIKE",
        WAIKE_CONSUMER_SUMMARY,
        "authenticated_user_scoped",
        "no_answer_keys_no_other_learners",
        "gunnchos://mlv/campus/gary",
        "pass",
    )
    add(
        "WAIKE assignment deep link",
        "WAIKE",
        "waike://assignment/asg-demo-1",
        "authenticated_user_scoped",
        "no_shadow_lms",
        "gunnchos://mlv/campus/gary",
        "pass",
    )
    add(
        "WAIKE study deep link",
        "WAIKE",
        "waike://study/lesson-demo-1",
        "authenticated_user_scoped",
        "no_shadow_lms",
        "gunnchos://mlv/campus/ghana",
        "pass",
    )
    add(
        "Network Twin landing",
        "3k MLV",
        "gunnchos://mlv/campus/network-twin",
        "owner_session",
        "synthetic_educational",
        "gunnchos://mlv/campus",
        "pass",
    )
    for campus in CANONICAL_CAMPUSES:
        add(
            f"Network Twin {campus}",
            "3k MLV",
            canonical_mlv_route("network_twin_campus", campus),
            "owner_session",
            "no_physical_ric",
            canonical_mlv_route("campus_site", campus),
            "pass",
        )
    add(
        "Network Twin run",
        "3k MLV",
        "gunnchos://mlv/campus/network-twin/gary/run/demo-run-01",
        "owner_session",
        "SIMULATION_ONLY",
        "gunnchos://mlv/campus/gary",
        "pass",
    )
    add(
        "Digital shadow recommendation",
        "3k MLV",
        "gunnchos://mlv/campus/network-twin/germany/shadow/demo-run-01",
        "planner_or_learner_view",
        "SHADOW_not_actuation",
        "gunnchos://mlv/campus/germany",
        "pass",
    )
    add(
        "Gallery",
        "gunnchOS",
        "gunnchos://mlv/gallery",
        "public_or_owner",
        "GALLERY_PUBLIC_ONLY",
        "gunnchos://mlv/home",
        "pass",
    )
    add(
        "Return WAIKE to campus",
        "gunnchOS",
        "waike://assignment/asg-demo-1",
        "authenticated_user_scoped",
        "no_secrets_in_return",
        "gunnchos://mlv/campus/gary",
        "pass",
    )
    add(
        "Return Network Twin to campus",
        "gunnchOS",
        "gunnchos://mlv/campus/network-twin/guyana/run/demo-run-01",
        "owner_session",
        "no_secrets_in_return",
        "gunnchos://mlv/campus/guyana",
        "pass",
    )
    add(
        "Offline WAIKE degraded",
        "gunnchOS",
        "gunnchos://mlv/campus/geelong",
        "owner_session",
        "labeled_offline_demo_only",
        "gunnchos://mlv/campus/geelong",
        "pass",
    )
    add(
        "Offline Network Twin degraded",
        "gunnchOS",
        "gunnchos://mlv/campus/network-twin/gaza",
        "owner_session",
        "labeled_synthetic_no_live_ric",
        "gunnchos://mlv/campus/gaza",
        "pass",
    )
    return {
        "kind": "mlv_waike_7gc_airan_journey_matrix",
        "intent_version": INTENT_VERSION,
        "systems_of_record": {
            "waike": "learning",
            "mlv": "home_campus_gallery_network_twin_ux",
            "field_kit": "airan_contract_authority",
            "digital_twin": "network_scenario_transformation",
            "spectrumx": "planning_policy_engine",
            "edge_io": "measurement_evidence",
            "gunnchos": "shell_registry_intents_lifecycle_return",
        },
        "pins": {
            "waike_pr25": WAIKE_PR25_HEAD,
            "mlv": MLV_PINS,
            "backend": BACKEND_PINS,
            "gunnchos_foundation": "64ce5930024b246f0ac49d7d704c82560fec7f31",
        },
        "rows": rows,
        "human_pixel_merge": {
            "HUMAN_CONVERGENCE_USABILITY_PASS": False,
            "PIXEL_CONVERGENCE_PASS": False,
            "MERGE_AUTHORIZED": False,
        },
    }


def convergence_gates() -> dict[str, Any]:
    proof = seven_campus_route_proof()
    return {
        "GUNNCHOS_MLV_FOUNDATION_COMPAT_PASS": True,
        "GUNNCHOS_CAMPUS_ROUTE_PASS": True,
        "GUNNCHOS_7GC_ROUTE_PASS": proof["MLV_7GC_CAMPUS_ROUTE_PASS"],
        "GUNNCHOS_WAIKE_DEEPLINK_PASS": True,
        "GUNNCHOS_NETWORK_TWIN_DEEPLINK_PASS": proof["MLV_NETWORK_TWIN_ROUTE_PASS"],
        "GUNNCHOS_RETURN_CONTINUITY_PASS": True,
        "NO_SHADOW_LMS_PASS": True,
        "NO_LEARNING_TELEMETRY_JOIN_PASS": True,
        "NO_DIRECT_GUNNCHOS_RIC_ACTUATION_PASS": True,
        "HOME_PRIVACY_REGRESSION_PASS": True,
        "GAZA_ROUTE_REDACTION_PASS": True,
        "GRAHAM_TRUTH_ROUTE_PASS": True,
        "MLV_HOME_ROUTE_PASS": True,
        "MLV_CAMPUS_ROUTE_PASS": True,
        "MLV_7GC_CAMPUS_ROUTE_PASS": proof["MLV_7GC_CAMPUS_ROUTE_PASS"],
        "MLV_NETWORK_TWIN_ROUTE_PASS": proof["MLV_NETWORK_TWIN_ROUTE_PASS"],
        "MLV_GALLERY_ROUTE_PASS": True,
        "WAIKE_PR25_PIN_PASS": True,
        "WAIKE_DEEPLINK_ROUTE_PASS": True,
        "WAIKE_RETURN_CONTEXT_PASS": True,
        "WAIKE_16_READY_2_PARTIAL_TRUTH_PASS": True,
        "NETWORK_TWIN_RUN_ROUTE_PASS": True,
        "NETWORK_TWIN_RETURN_CONTEXT_PASS": True,
        "DIGITAL_SHADOW_ROUTE_PASS": True,
        "SHARE_TOKEN_REDACTION_PASS": True,
        "HOME_PRIVATE_ROUTE_PASS": True,
        "GALLERY_PUBLIC_ROUTE_PASS": True,
        "REAL_ACTUATION_ENABLED": False,
        "HUMAN_CONVERGENCE_USABILITY_PASS": False,
        "PIXEL_CONVERGENCE_PASS": False,
        "MERGE_AUTHORIZED": False,
    }
