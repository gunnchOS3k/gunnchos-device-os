#!/usr/bin/env python3
"""CX3.3 Education/Career digital closure provider."""

from __future__ import annotations

import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlparse

ROOT = Path(os.environ.get("CX33_ROOT", "/var/lib/cx3_3"))
WALLET_ROOT = Path(os.environ.get("CX33_WALLET_ROOT", str(ROOT / "wallet")))
PORTFOLIO_ROOT = Path(os.environ.get("CX33_PORTFOLIO_ROOT", str(ROOT / "portfolio")))
CAREER_ROOT = Path(os.environ.get("CX33_CAREER_ROOT", str(ROOT / "career")))
SHARE_ROOT = Path(os.environ.get("CX33_SHARE_ROOT", str(ROOT / "share")))
EDU_ROOT = Path(os.environ.get("CX33_EDUCATION_ROOT", str(ROOT / "education")))
SKILL_ROOT = Path(os.environ.get("CX33_SKILL_GRAPH_ROOT", str(ROOT / "skill_graph")))
PKG_ROOT = Path(os.environ.get("CX33_CAREER_PACKAGE_ROOT", str(ROOT / "career_package")))
VERIFIER_CACHE = Path(os.environ.get("CX33_VERIFIER_CACHE", str(ROOT / "verifier_cache")))
HOST = os.environ.get("CX33_BIND", "127.0.0.1")
PORT = int(os.environ.get("CX33_PORT", "8773"))
STATE: Dict[str, Any] = {"events": [], "last_package_dir": None}


def _bootstrap() -> None:
    repo = os.environ.get("CX33_REPO")
    if repo:
        sys.path.insert(0, repo)


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class Handler(BaseHTTPRequestHandler):
    server_version = "cx3_3-digital-closure/1.0"

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
                        "provider": "cx3_3-digital-closure",
                        "certification_claimed": False,
                        "port": PORT,
                    },
                )
            if path == "/api/education/get":
                from gunnchos_device_os.cx3_3.education import EducationTimelineStore

                return self._json(
                    200,
                    {"ok": True, "timeline": EducationTimelineStore(EDU_ROOT).get(), "certification_claimed": False},
                )
            if path == "/api/skill_graph/get":
                from gunnchos_device_os.cx3_3.skill_graph import SkillEvidenceGraph

                return self._json(
                    200,
                    {"ok": True, "graph": SkillEvidenceGraph(SKILL_ROOT).get(), "certification_claimed": False},
                )
            if path == "/api/career/get":
                from gunnchos_device_os.cx3_2.career import CareerProfileStore

                return self._json(
                    200,
                    {"ok": True, "profile": CareerProfileStore(CAREER_ROOT).get(), "certification_claimed": False},
                )
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
            if path == "/api/journey/education_timeline":
                from gunnchos_device_os.cx3.wallet import CredentialWallet
                from gunnchos_device_os.cx3_3.education import EducationTimelineStore

                edu = EducationTimelineStore(EDU_ROOT)
                if not edu.get():
                    edu.create()
                wallet = CredentialWallet(WALLET_ROOT)
                status_map = wallet.status_map()
                active = [
                    c
                    for c in wallet.list()
                    if status_map.get(c.get("credential_id"), "active") not in ("revoked", "expired")
                ]
                if active:
                    edu.add_entry(
                        {
                            "label": active[0].get("name") or "Credential achievement",
                            "kind": "achievement",
                        },
                        gui_action=True,
                        verified_credential=active[0],
                    )
                edu.add_entry(
                    {
                        "label": payload.get("user_label") or "Self-reported education",
                        "kind": "education",
                        "source": "user_entered",
                        "verified": False,
                    },
                    gui_action=True,
                )
                doc = edu.get()
                return self._json(
                    200,
                    {
                        "ok": bool(doc) and (edu.distinguishes_verified() or bool(active)),
                        "timeline": doc,
                        "certification_claimed": False,
                    },
                )
            if path == "/api/journey/skill_graph":
                from gunnchos_device_os.cx3.portfolio import PortfolioStore
                from gunnchos_device_os.cx3.wallet import CredentialWallet
                from gunnchos_device_os.cx3_2.career import CareerProfileStore
                from gunnchos_device_os.cx3_3.skill_graph import SkillEvidenceGraph

                graph = SkillEvidenceGraph(SKILL_ROOT)
                profile = CareerProfileStore(CAREER_ROOT).get() or {}
                # Compose skills via sidecar labels from profile (do not mutate signed creds)
                creds = []
                for c in CredentialWallet(WALLET_ROOT).list():
                    cc = dict(c)
                    cc["skills"] = ["evidence binding"] if not creds else ["offline verify"]
                    creds.append(cc)
                doc = graph.build(
                    credentials=creds,
                    artifacts=PortfolioStore(PORTFOLIO_ROOT).list_artifacts(),
                    user_skills=list(profile.get("skills") or ["self study"]),
                )
                explain = graph.explain((doc.get("skills") or [{}])[0].get("label") or "evidence binding")
                return self._json(
                    200,
                    {"ok": True, "graph": doc, "explain": explain, "certification_claimed": False},
                )
            if path == "/api/journey/career_profile":
                from gunnchos_device_os.cx3.portfolio import PortfolioStore
                from gunnchos_device_os.cx3.wallet import CredentialWallet
                from gunnchos_device_os.cx3_2.career import CareerProfileStore

                c = CareerProfileStore(CAREER_ROOT)
                arts = [a for a in PortfolioStore(PORTFOLIO_ROOT).list_artifacts() if a.get("visibility") != "private"]
                profile = c.create_or_update(
                    {
                        "display_name": "Lab Student",
                        "headline": payload.get("headline") or "CX3.3 career profile",
                        "summary": payload.get("summary") or "Education/career digital closure journey",
                        "skills": ["evidence binding", "self study"],
                        "credential_refs": [x["credential_id"] for x in CredentialWallet(WALLET_ROOT).list()[:1]],
                        "artifact_refs": [a["artifact_id"] for a in arts[:2]],
                        "projects": [
                            {
                                "title": "CX3.3 closure",
                                "summary": "User-authored",
                                "source": "user_entered",
                                "verified": False,
                            }
                        ],
                        "visibility": {"contact": "private", "display_name": "public_local", "headline": "public_local", "summary": "public_local", "skills": "public_local"},
                    },
                    gui_action=True,
                )
                return self._json(200, {"ok": True, "profile": profile, "certification_claimed": False})
            if path == "/api/journey/career_package":
                from gunnchos_device_os.cx3.portfolio import PortfolioStore
                from gunnchos_device_os.cx3.wallet import CredentialWallet
                from gunnchos_device_os.cx3_2.career import CareerProfileStore
                from gunnchos_device_os.cx3_2.resume import export_resume
                from gunnchos_device_os.cx3_3.career_package import build_career_package
                from gunnchos_device_os.cx3_3.education import EducationTimelineStore
                from gunnchos_device_os.cx3_3.skill_graph import SkillEvidenceGraph

                career = CareerProfileStore(CAREER_ROOT)
                profile = career.get()
                if not profile:
                    return self._json(400, {"ok": False, "blocker": "no_profile"})
                public = career.public_view(
                    include_fields=[
                        "display_name",
                        "headline",
                        "summary",
                        "skills",
                        "projects",
                        "credential_refs",
                        "artifact_refs",
                    ]
                )
                resume = export_resume(
                    profile,
                    out_dir=ROOT / "resume",
                    include_fields=["display_name", "headline", "summary", "skills", "projects"],
                    credentials=CredentialWallet(WALLET_ROOT).list(),
                    artifacts=PortfolioStore(PORTFOLIO_ROOT).list_artifacts(),
                )
                arts = [
                    a
                    for a in PortfolioStore(PORTFOLIO_ROOT).list_artifacts()
                    if a.get("visibility") != "private"
                ][:1]
                pkg = build_career_package(
                    out_dir=PKG_ROOT,
                    career_public=public,
                    resume_meta=resume,
                    credentials=CredentialWallet(WALLET_ROOT).list(),
                    artifacts=arts,
                    education_timeline=EducationTimelineStore(EDU_ROOT).get(),
                    skill_graph=SkillEvidenceGraph(SKILL_ROOT).get(),
                    excluded_fields=["contact"],
                )
                STATE["last_package_dir"] = pkg.get("package_dir")
                return self._json(200, {**pkg, "certification_claimed": False})
            if path == "/api/journey/recovery":
                from gunnchos_device_os.cx3_3.recovery import recover_from_package

                pkg_dir = payload.get("package_dir") or STATE.get("last_package_dir")
                if not pkg_dir:
                    return self._json(400, {"ok": False, "blocker": "no_package"})
                result = recover_from_package(
                    Path(pkg_dir),
                    dest_root=ROOT / "recovery_profile",
                    verifier_cache=VERIFIER_CACHE / "recovery",
                )
                return self._json(200, result)
            if path == "/api/journey/verifier":
                from gunnchos_device_os.cx3_2.share import build_share_package
                from gunnchos_device_os.cx3_2.verifier import IndependentVerifier
                from gunnchos_device_os.cx3.wallet import CredentialWallet
                from gunnchos_device_os.cx3_2.career import CareerProfileStore

                career = CareerProfileStore(CAREER_ROOT)
                public = career.public_view(include_fields=["display_name", "headline", "summary", "skills"])
                wallet = CredentialWallet(WALLET_ROOT)
                share = build_share_package(
                    career_public=public,
                    credentials=wallet.list()[:1],
                    artifacts=[],
                    out_dir=SHARE_ROOT,
                    excluded_fields=["contact"],
                    status_map=wallet.status_map(),
                )
                v = IndependentVerifier(VERIFIER_CACHE)
                result = v.verify_package(share["package"], wallet_root_forbidden=WALLET_ROOT)
                return self._json(
                    200,
                    {
                        "ok": bool(result.get("ok")) and result.get("wallet_db_used") is False,
                        **result,
                        "certification_claimed": False,
                    },
                )
            return self._json(404, {"ok": False, "blocker": "not_found"})
        except Exception as exc:  # noqa: BLE001
            return self._json(500, {"ok": False, "blocker": type(exc).__name__, "detail": str(exc)})


def main() -> None:
    _bootstrap()
    for p in (ROOT, WALLET_ROOT, PORTFOLIO_ROOT, CAREER_ROOT, SHARE_ROOT, EDU_ROOT, SKILL_ROOT, PKG_ROOT, VERIFIER_CACHE):
        Path(p).mkdir(parents=True, exist_ok=True)
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    sys.stderr.write(f"cx3_3 provider on http://{HOST}:{PORT}\n")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
