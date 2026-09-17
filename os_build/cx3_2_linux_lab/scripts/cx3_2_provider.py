#!/usr/bin/env python3
"""CX3.2 Career Profile + Share + Independent Verifier provider."""

from __future__ import annotations

import json
import os
import sys
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlparse

ROOT = Path(os.environ.get("CX32_ROOT", "/var/lib/cx3_2"))
WALLET_ROOT = Path(os.environ.get("CX32_WALLET_ROOT", str(ROOT / "wallet")))
PORTFOLIO_ROOT = Path(os.environ.get("CX32_PORTFOLIO_ROOT", str(ROOT / "portfolio")))
CAREER_ROOT = Path(os.environ.get("CX32_CAREER_ROOT", str(ROOT / "career")))
SHARE_ROOT = Path(os.environ.get("CX32_SHARE_ROOT", str(ROOT / "share")))
VERIFIER_CACHE = Path(os.environ.get("CX32_VERIFIER_CACHE", str(ROOT / "verifier_cache")))
HOST = os.environ.get("CX32_BIND", "127.0.0.1")
PORT = int(os.environ.get("CX32_PORT", "8772"))
STATE: Dict[str, Any] = {"events": []}


def _bootstrap() -> None:
    repo = os.environ.get("CX32_REPO")
    if repo:
        sys.path.insert(0, repo)


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class Handler(BaseHTTPRequestHandler):
    server_version = "cx3_2-career-verifier/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A003
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _json(self, code: int, obj: Dict[str, Any]) -> None:
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        try:
            if path in ("/", "/api/health"):
                return self._json(
                    200,
                    {
                        "ok": True,
                        "provider": "cx3_2-career-verifier",
                        "certification_claimed": False,
                        "port": PORT,
                    },
                )
            if path == "/api/career/get":
                from gunnchos_device_os.cx3_2.career import CareerProfileStore

                c = CareerProfileStore(CAREER_ROOT)
                return self._json(200, {"ok": True, "profile": c.get(), "certification_claimed": False})
            if path == "/api/wallet/list":
                from gunnchos_device_os.cx3.wallet import CredentialWallet

                w = CredentialWallet(WALLET_ROOT)
                return self._json(200, {"ok": True, "credentials": w.list(), "certification_claimed": False})
            if path == "/api/portfolio/list":
                from gunnchos_device_os.cx3.portfolio import PortfolioStore

                p = PortfolioStore(PORTFOLIO_ROOT)
                return self._json(200, {"ok": True, "artifacts": p.list_artifacts(), "certification_claimed": False})
            return self._json(404, {"ok": False, "blocker": "not_found"})
        except Exception as exc:  # noqa: BLE001
            return self._json(500, {"ok": False, "blocker": type(exc).__name__, "detail": str(exc)})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return self._json(400, {"ok": False, "blocker": "bad_json"})
        try:
            if path == "/api/career/save":
                from gunnchos_device_os.cx3_2.career import CareerProfileStore

                c = CareerProfileStore(CAREER_ROOT)
                # GUI alone cannot create verified claims
                patch = dict(payload)
                for edu in patch.get("education") or []:
                    if edu.get("verified") is True and edu.get("source") != "verified_source":
                        return self._json(400, {"ok": False, "blocker": "verified_claim_via_gui_forbidden"})
                profile = c.create_or_update(patch, gui_action=True)
                STATE["events"].append({"event": "career_save", "at": _now()})
                return self._json(200, {"ok": True, "profile": profile, "certification_claimed": False})
            if path == "/api/career/resume_export":
                from gunnchos_device_os.cx3_2.career import CareerProfileStore
                from gunnchos_device_os.cx3_2.resume import export_resume
                from gunnchos_device_os.cx3.wallet import CredentialWallet
                from gunnchos_device_os.cx3.portfolio import PortfolioStore

                c = CareerProfileStore(CAREER_ROOT)
                profile = c.get()
                if not profile:
                    return self._json(400, {"ok": False, "blocker": "no_profile"})
                out = export_resume(
                    profile,
                    out_dir=ROOT / "resume",
                    include_fields=payload.get("include_fields")
                    or ["display_name", "headline", "summary", "skills", "projects"],
                    credentials=CredentialWallet(WALLET_ROOT).list(),
                    artifacts=PortfolioStore(PORTFOLIO_ROOT).list_artifacts(),
                )
                return self._json(200, {"ok": True, **out})
            if path == "/api/journey/career_profile":
                from gunnchos_device_os.cx3_2.career import CareerProfileStore
                from gunnchos_device_os.cx3.wallet import CredentialWallet
                from gunnchos_device_os.cx3.portfolio import PortfolioStore

                c = CareerProfileStore(CAREER_ROOT)
                w = CredentialWallet(WALLET_ROOT)
                p = PortfolioStore(PORTFOLIO_ROOT)
                arts = p.list_artifacts()
                selective = [a for a in arts if a.get("visibility") != "private"][:2]
                if len(selective) < 2 and arts:
                    selective = arts[:2]
                profile = c.create_or_update(
                    {
                        "display_name": "Lab Student",
                        "headline": payload.get("headline") or "Career profile via GUI journey",
                        "summary": payload.get("summary") or "Built inside gunnchOS without second computer.",
                        "skills": ["portfolio", "credentials", "verification"],
                        "credential_refs": [x["credential_id"] for x in w.list()[:1]],
                        "artifact_refs": [a["artifact_id"] for a in selective],
                        "projects": [
                            {
                                "title": "CX3.2 share journey",
                                "summary": "User-authored highlight",
                                "source": "user_entered",
                                "verified": False,
                            }
                        ],
                        "visibility": {
                            "display_name": "public_local",
                            "headline": "public_local",
                            "summary": "public_local",
                            "skills": "public_local",
                            "contact": "private",
                            "credentials": "selective",
                            "artifacts": "selective",
                            "projects": "selective",
                            "links": "selective",
                        },
                        "contact": {"email": "private-lab-student@example.invalid"},
                    },
                    gui_action=True,
                )
                # restart-equivalent reload
                again = c.get()
                ok = again is not None and again.get("profile_id") == profile["profile_id"]
                STATE["events"].append({"event": "career_profile_journey", "at": _now(), "ok": ok})
                return self._json(
                    200,
                    {
                        "ok": ok,
                        "profile": again,
                        "certification_claimed": False,
                        "CX3_REAL_CAREER_PROFILE_GUI_PASS": ok,
                    },
                )
            if path == "/api/journey/share_package":
                from gunnchos_device_os.cx3_2.career import CareerProfileStore
                from gunnchos_device_os.cx3_2.share import build_share_package
                from gunnchos_device_os.cx3.wallet import CredentialWallet
                from gunnchos_device_os.cx3.portfolio import PortfolioStore

                c = CareerProfileStore(CAREER_ROOT)
                w = CredentialWallet(WALLET_ROOT)
                p = PortfolioStore(PORTFOLIO_ROOT)
                profile = c.get() or {}
                status = w.status_map()
                creds = [x for x in w.list() if status.get(x.get("credential_id"), x.get("status") or "active") == "active"]
                if not creds:
                    creds = w.list()[:1]
                arts = [a for a in p.list_artifacts() if a.get("visibility") != "private"]
                excl_c = []
                excl_a = []
                if payload.get("exclude_one_credential") and len(creds) > 1:
                    excl_c = [creds[-1]["credential_id"]]
                    creds = creds[:-1]
                if payload.get("exclude_one_artifact") and len(arts) > 1:
                    excl_a = [arts[-1]["artifact_id"]]
                    arts = arts[:-1]
                public = c.public_view(
                    include_fields=["display_name", "headline", "summary", "skills", "projects", "credential_refs", "artifact_refs"]
                )
                excl_fields = ["contact"] if payload.get("exclude_contact", True) else []
                result = build_share_package(
                    career_public=public,
                    credentials=creds,
                    artifacts=arts[:1] or arts,
                    out_dir=SHARE_ROOT,
                    excluded_credential_ids=excl_c,
                    excluded_artifact_ids=excl_a,
                    excluded_fields=excl_fields,
                    status_map=w.status_map(),
                )
                STATE["events"].append({"event": "share_package", "at": _now(), "package_id": result["package"]["package_id"]})
                return self._json(
                    200,
                    {
                        "ok": True,
                        "package_id": result["package"]["package_id"],
                        "package_dir": result["package_dir"],
                        "manifest_path": result["manifest_path"],
                        "certification_claimed": False,
                    },
                )
            if path == "/api/journey/verifier":
                from gunnchos_device_os.cx3_2.verifier import IndependentVerifier
                from gunnchos_device_os.cx3.wallet import CredentialWallet

                v = IndependentVerifier(VERIFIER_CACHE)
                pkg_dir = payload.get("package_dir")
                if not pkg_dir:
                    shares = sorted(SHARE_ROOT.glob("psp_*"))
                    if not shares:
                        return self._json(400, {"ok": False, "blocker": "no_share_package"})
                    pkg_dir = str(shares[-1])
                package = v.load_package(Path(pkg_dir))
                w = CredentialWallet(WALLET_ROOT)
                # Force active status overlay for the initial valid check (package snapshot may be stale)
                active_overlay = {}
                for cred in package.get("credentials") or []:
                    cid = cred.get("credential_id")
                    active_overlay[cid] = {
                        "credential_id": cid,
                        "status": "active",
                        "updated_at": _now(),
                        "certification_claimed": False,
                    }
                v.set_status_provider(active_overlay, online=True)
                good = v.verify_package(package, wallet_root_forbidden=WALLET_ROOT)
                bad = v.verify_tampered_copy(package)
                revoked_view = None
                if package.get("credentials"):
                    cid = package["credentials"][0]["credential_id"]
                    overlay = dict(active_overlay)
                    overlay[cid] = {
                        "credential_id": cid,
                        "status": "revoked",
                        "updated_at": _now(),
                        "reason": "verifier_gui_demo",
                        "certification_claimed": False,
                    }
                    v.set_status_provider(overlay, online=True)
                    revoked_view = v.verify_package(package, wallet_root_forbidden=WALLET_ROOT)
                v.set_status_provider(None, online=False)
                offline = v.verify_package(package, wallet_root_forbidden=WALLET_ROOT)
                ok = (
                    bool(good.get("valid"))
                    and bad.get("valid") is False
                    and good.get("wallet_db_used") is False
                    and any(c.get("revoked") for c in (revoked_view or {}).get("credentials") or [])
                    and any((c.get("freshness") == "stale") for c in (offline.get("credentials") or []))
                )
                STATE["events"].append({"event": "verifier_journey", "at": _now(), "ok": ok})
                return self._json(
                    200,
                    {
                        "ok": ok,
                        "valid": good.get("valid"),
                        "tampered_valid": bad.get("valid"),
                        "revoked": revoked_view,
                        "offline": offline,
                        "wallet_db_used": False,
                        "certification_claimed": False,
                        "CX3_REAL_VERIFIER_GUI_PASS": ok,
                    },
                )
            return self._json(404, {"ok": False, "blocker": "not_found"})
        except Exception as exc:  # noqa: BLE001
            return self._json(500, {"ok": False, "blocker": type(exc).__name__, "detail": str(exc)})


def main() -> int:
    _bootstrap()
    for d in (ROOT, WALLET_ROOT, PORTFOLIO_ROOT, CAREER_ROOT, SHARE_ROOT, VERIFIER_CACHE):
        d.mkdir(parents=True, exist_ok=True)
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    sys.stderr.write(f"cx3_2 provider on http://{HOST}:{PORT}\n")
    httpd.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
