"""Versioned API/ABI policy + negotiation/deprecation/compatibility (Lane G)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import re

from gunnchos_device_os.cont_viii import CLAIM_BOUNDARY, TOKEN_API_ABI_PASS

SURFACES = (
    "app_manifest",
    "permissions",
    "device_role",
    "ring_input",
    "ai",
    "connectivity",
    "telemetry",
    "fleet",
    "save_cloud",
)

SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:[-+][0-9A-Za-z.-]+)?$")

CURRENT = {
    "app_manifest": "1.2.0",
    "permissions": "1.1.0",
    "device_role": "1.0.0",
    "ring_input": "1.3.0",
    "ai": "1.0.0",
    "connectivity": "1.1.0",
    "telemetry": "1.0.0",
    "fleet": "1.0.0",
    "save_cloud": "1.0.0",
}

# Deprecated minors still accepted during grace
DEPRECATED = {
    "app_manifest": ["1.0.0", "1.1.0"],
    "ring_input": ["1.0.0", "1.1.0"],
}

# Hard floors — below rejected
MIN_SUPPORTED = {
    "app_manifest": "1.0.0",
    "permissions": "1.0.0",
    "device_role": "1.0.0",
    "ring_input": "1.0.0",
    "ai": "1.0.0",
    "connectivity": "1.0.0",
    "telemetry": "1.0.0",
    "fleet": "1.0.0",
    "save_cloud": "1.0.0",
}


def parse_semver(v: str) -> tuple[int, int, int]:
    m = SEMVER.match(v)
    if not m:
        raise ValueError(f"invalid semver: {v}")
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def cmp_semver(a: str, b: str) -> int:
    aa, bb = parse_semver(a), parse_semver(b)
    return (aa > bb) - (aa < bb)


@dataclass
class ApiAbiNegotiator:
    current: dict[str, str] = field(default_factory=lambda: dict(CURRENT))
    deprecated: dict[str, list[str]] = field(default_factory=lambda: {k: list(v) for k, v in DEPRECATED.items()})
    min_supported: dict[str, str] = field(default_factory=lambda: dict(MIN_SUPPORTED))

    def negotiate(self, surface: str, requested: str) -> dict[str, Any]:
        if surface not in SURFACES:
            return {"ok": False, "reason": "unknown_surface", "surface": surface}
        if not SEMVER.match(requested):
            return {"ok": False, "reason": "invalid_semver", "requested": requested}
        cur = self.current[surface]
        floor = self.min_supported[surface]
        if cmp_semver(requested, floor) < 0:
            return {
                "ok": False,
                "surface": surface,
                "requested": requested,
                "reason": "below_min_supported",
                "min_supported": floor,
                "compatibility": "incompatible",
            }
        if requested in self.deprecated.get(surface, []):
            return {
                "ok": True,
                "surface": surface,
                "requested": requested,
                "negotiated": requested,
                "compatibility": "deprecated_accepted",
                "deprecation": True,
                "upgrade_to": cur,
            }
        # same major required
        if parse_semver(requested)[0] != parse_semver(cur)[0]:
            return {
                "ok": False,
                "surface": surface,
                "requested": requested,
                "reason": "major_mismatch",
                "current": cur,
                "compatibility": "incompatible",
            }
        if cmp_semver(requested, cur) <= 0:
            return {
                "ok": True,
                "surface": surface,
                "requested": requested,
                "negotiated": requested,
                "compatibility": "compatible",
                "deprecation": False,
                "current": cur,
            }
        # newer minor from future client — accept if same major (forward-tolerant read)
        return {
            "ok": True,
            "surface": surface,
            "requested": requested,
            "negotiated": cur,
            "compatibility": "forward_tolerant_server_caps",
            "deprecation": False,
            "current": cur,
        }

    def compatibility_matrix(self) -> dict[str, Any]:
        matrix = {}
        for surface in SURFACES:
            cur = self.current[surface]
            cases = [
                self.negotiate(surface, cur),
                self.negotiate(surface, self.min_supported[surface]),
                self.negotiate(surface, "0.0.1"),
                self.negotiate(surface, f"{parse_semver(cur)[0]+1}.0.0"),
            ]
            for dep in self.deprecated.get(surface, [])[:1]:
                cases.append(self.negotiate(surface, dep))
            matrix[surface] = cases
        return matrix

    def evaluate(self) -> dict[str, Any]:
        matrix = self.compatibility_matrix()
        # Policy must reject 0.0.1 and next-major for every surface
        ok = True
        for surface, cases in matrix.items():
            rejects = [c for c in cases if not c.get("ok")]
            accepts_current = any(c.get("ok") and c.get("requested") == self.current[surface] for c in cases)
            if len(rejects) < 2 or not accepts_current:
                ok = False
        return {
            "schema": "gunnchos.api_abi_policy.v1",
            "ok": ok,
            "token": TOKEN_API_ABI_PASS if ok else None,
            "surfaces": list(SURFACES),
            "current": self.current,
            "deprecated": self.deprecated,
            "min_supported": self.min_supported,
            "matrix": matrix,
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }


def evaluate_api_abi_policy() -> dict[str, Any]:
    return ApiAbiNegotiator().evaluate()
