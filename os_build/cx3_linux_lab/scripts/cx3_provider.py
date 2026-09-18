#!/usr/bin/env python3
"""CX3 Wallet + Portfolio provider (guest or host loopback).

Serves Wallet and Portfolio authorities for the shell GUI.
Never sets certification_claimed=true.
"""

from __future__ import annotations

import json
import os
import sys
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

# Allow running as standalone script in guest without package install.
ROOT = Path(os.environ.get("CX3_ROOT", "/var/lib/cx3"))
WALLET_ROOT = Path(os.environ.get("CX3_WALLET_ROOT", str(ROOT / "wallet")))
PORTFOLIO_ROOT = Path(os.environ.get("CX3_PORTFOLIO_ROOT", str(ROOT / "portfolio")))
HOST = os.environ.get("CX3_BIND", "127.0.0.1")
PORT = int(os.environ.get("CX3_PORT", "8771"))


def _bootstrap_package() -> None:
    """When executed from Device OS tree, import real authorities."""
    repo = os.environ.get("CX3_REPO")
    if repo:
        sys.path.insert(0, repo)
    try:
        from gunnchos_device_os.cx3.wallet import CredentialWallet  # noqa: F401
        from gunnchos_device_os.cx3.portfolio import PortfolioStore  # noqa: F401
        from gunnchos_device_os.cx3.issuer import (  # noqa: F401
            create_ephemeral_issuer,
            issue_evidence_bound_credential,
            verify_credential,
            detect_tamper,
        )
        from gunnchos_device_os.cx3.vault_bind import load_vault_evidence  # noqa: F401

        return
    except Exception:
        pass


STATE: Dict[str, Any] = {"journey_events": []}


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class Handler(BaseHTTPRequestHandler):
    server_version = "cx3-wallet-portfolio/1.0"

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
                        "provider": "cx3-wallet-portfolio",
                        "certification_claimed": False,
                        "port": PORT,
                    },
                )
            if path == "/api/wallet/list":
                from gunnchos_device_os.cx3.wallet import CredentialWallet

                w = CredentialWallet(WALLET_ROOT)
                return self._json(
                    200,
                    {
                        "ok": True,
                        "credentials": w.list(),
                        "certification_claimed": False,
                        "provider": "cx3-wallet",
                    },
                )
            if path.startswith("/api/wallet/verify/"):
                from gunnchos_device_os.cx3.wallet import CredentialWallet

                cid = path.split("/api/wallet/verify/", 1)[1]
                w = CredentialWallet(WALLET_ROOT)
                return self._json(200, {"ok": True, **w.verify(cid, offline=True)})
            if path == "/api/portfolio/list":
                from gunnchos_device_os.cx3.portfolio import PortfolioStore

                p = PortfolioStore(PORTFOLIO_ROOT)
                return self._json(
                    200,
                    {
                        "ok": True,
                        "artifacts": p.list_artifacts(),
                        "certification_claimed": False,
                        "provider": "cx3-portfolio",
                    },
                )
            if path == "/api/journey":
                return self._json(
                    200,
                    {
                        "ok": True,
                        "events": STATE.get("journey_events", []),
                        "certification_claimed": False,
                    },
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
            if path == "/api/wallet/issue_demo":
                return self._json(200, self._issue_demo(payload))
            if path == "/api/wallet/revoke":
                from gunnchos_device_os.cx3.wallet import CredentialWallet

                w = CredentialWallet(WALLET_ROOT)
                return self._json(200, w.revoke(payload.get("credential_id") or "", reason="ui_revoke"))
            if path == "/api/wallet/export":
                from gunnchos_device_os.cx3.wallet import CredentialWallet

                w = CredentialWallet(WALLET_ROOT)
                export = w.export_credentials(payload.get("credential_ids"))
                out = ROOT / "exports"
                out.mkdir(parents=True, exist_ok=True)
                path_out = out / f"{export['export_id']}.json"
                path_out.write_text(json.dumps(export, indent=2) + "\n")
                STATE["journey_events"].append({"event": "wallet_export", "at": _now()})
                return self._json(200, {"ok": True, "export": export, "path": str(path_out)})
            if path == "/api/wallet/import":
                from gunnchos_device_os.cx3.wallet import CredentialWallet

                w = CredentialWallet(WALLET_ROOT)
                result = w.import_credentials(payload.get("export") or payload)
                STATE["journey_events"].append({"event": "wallet_import", "at": _now(), "ok": result.get("ok")})
                return self._json(200, result)
            if path == "/api/portfolio/export":
                from gunnchos_device_os.cx3.portfolio import PortfolioStore
                from gunnchos_device_os.cx3.wallet import CredentialWallet

                p = PortfolioStore(PORTFOLIO_ROOT)
                w = CredentialWallet(WALLET_ROOT)
                ids = payload.get("selected_artifact_ids") or []
                result = p.selective_export(ids, title=payload.get("title") or "Portable portfolio", credentials=w.list())
                STATE["journey_events"].append({"event": "portfolio_export", "at": _now()})
                return self._json(200, result)
            if path == "/api/journey/signed_credential":
                # Full signed credential journey as exercised by GUI
                demo = self._issue_demo({})
                if not demo.get("ok"):
                    return self._json(200, demo)
                from gunnchos_device_os.cx3.wallet import CredentialWallet
                from gunnchos_device_os.cx3.issuer import detect_tamper

                w = CredentialWallet(WALLET_ROOT)
                cid = demo["credential"]["credential_id"]
                verify = w.verify(cid, offline=True)
                tamper = detect_tamper(demo["credential"])
                STATE["journey_events"].append(
                    {
                        "event": "signed_credential_journey",
                        "at": _now(),
                        "credential_id": cid,
                        "verified": verify.get("verified"),
                        "tamper_detected": tamper.get("tamper_detected"),
                        "certification_claimed": False,
                    }
                )
                return self._json(
                    200,
                    {
                        "ok": bool(verify.get("verified")) and bool(tamper.get("tamper_detected")),
                        "credential": demo["credential"],
                        "verify": verify,
                        "tamper": tamper,
                        "certification_claimed": False,
                        "CX3_SIGNED_CREDENTIAL_JOURNEY_PASS": bool(verify.get("verified")),
                    },
                )
            return self._json(404, {"ok": False, "blocker": "not_found"})
        except Exception as exc:  # noqa: BLE001
            return self._json(500, {"ok": False, "blocker": type(exc).__name__, "detail": str(exc)})

    def _issue_demo(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        from gunnchos_device_os.cx3.issuer import create_ephemeral_issuer, issue_evidence_bound_credential
        from gunnchos_device_os.cx3.wallet import CredentialWallet
        from gunnchos_device_os.cx3.portfolio import PortfolioStore

        evidence = payload.get("evidence")
        if not evidence:
            evidence = {
                "evidence_id": f"ev:ui:{uuid.uuid4().hex[:10]}",
                "source": "vault",
                "artifact_sha256": os.environ.get(
                    "CX3_VAULT_SHA256",
                    "e72f5b8c2940c253d8dc7d7797318de2a0fa2b394f0d4caca1e6495b87e13fd6",
                ),
                "artifact_path": os.environ.get("CX3_VAULT_PATH", "cx2h2_j1_essay.odt"),
                "captured_at": _now(),
                "mime": "application/vnd.oasis.opendocument.text",
                "certification_claimed": False,
            }
        issuer = create_ephemeral_issuer(name="CX3 UI Lab Issuer")
        cred = issue_evidence_bound_credential(
            issuer,
            subject_profile_id=payload.get("subject_profile_id") or "profile:lab-student",
            evidence=evidence,
        )
        w = CredentialWallet(WALLET_ROOT)
        w.put(cred)
        p = PortfolioStore(PORTFOLIO_ROOT)
        art = p.upsert_artifact(
            {
                "title": payload.get("artifact_title") or "Signed credential journey artifact",
                "visibility": "selective",
                "linked_credential_ids": [cred["credential_id"]],
                "summary": "Created via Wallet GUI journey — certification_claimed=false",
                "evidence_refs": [evidence["evidence_id"]],
            }
        )
        STATE["journey_events"].append(
            {
                "event": "issue_demo",
                "at": _now(),
                "credential_id": cred["credential_id"],
                "artifact_id": art["artifact_id"],
                "certification_claimed": False,
            }
        )
        return {
            "ok": True,
            "credential": cred,
            "artifact": art,
            "issuer": issuer.profile(),
            "certification_claimed": False,
        }


def main() -> int:
    _bootstrap_package()
    WALLET_ROOT.mkdir(parents=True, exist_ok=True)
    PORTFOLIO_ROOT.mkdir(parents=True, exist_ok=True)
    ROOT.mkdir(parents=True, exist_ok=True)
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    sys.stderr.write(f"cx3 provider on http://{HOST}:{PORT} wallet={WALLET_ROOT}\n")
    httpd.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
