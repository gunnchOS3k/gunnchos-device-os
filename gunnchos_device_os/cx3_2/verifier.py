"""Independent Credential / Portfolio Verifier — no Wallet DB dependency."""

from __future__ import annotations

import copy
import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

from gunnchos_device_os.cx3.issuer import verify_credential


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _sha(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(raw).hexdigest()


def _normalize_status_map(status_map: Optional[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    if not status_map:
        return out
    for cid, raw in status_map.items():
        if isinstance(raw, str):
            out[cid] = {
                "credential_id": cid,
                "status": raw,
                "updated_at": _now(),
                "certification_claimed": False,
            }
        elif isinstance(raw, dict):
            item = dict(raw)
            item.setdefault("credential_id", cid)
            item.setdefault("certification_claimed", False)
            out[cid] = item
    return out


class IndependentVerifier:
    """Verifier that works from exported package bytes only.

    Explicitly refuses to open Wallet internal DB paths as authority.
    """

    def __init__(self, cache_dir: Path):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._status_provider: Optional[Dict[str, Any]] = None
        self._status_online = True

    def refuse_wallet_db(self, wallet_root: Optional[Path]) -> Dict[str, Any]:
        return {
            "ok": True,
            "wallet_db_used": False,
            "refused_path": str(wallet_root) if wallet_root else None,
            "note": "Independent verifier does not read Wallet DB as authority",
        }

    def set_status_provider(self, status_map: Optional[Dict[str, Any]], *, online: bool = True) -> None:
        self._status_provider = _normalize_status_map(status_map) if status_map is not None else None
        self._status_online = online

    def load_package(self, path: Path) -> Dict[str, Any]:
        path = Path(path)
        if path.is_dir():
            path = path / "manifest.json"
        data = json.loads(path.read_text())
        if data.get("certification_claimed") is True:
            raise ValueError("reject_certification_claimed_true")
        if data.get("format") != "gunnchos.portfolio_share_package.v1":
            raise ValueError("reject_unknown_format")
        return data

    def verify_package(
        self,
        package: Dict[str, Any],
        *,
        wallet_root_forbidden: Optional[Path] = None,
    ) -> Dict[str, Any]:
        refuse = self.refuse_wallet_db(wallet_root_forbidden)
        if package.get("certification_claimed") is not False:
            return {
                "ok": False,
                "valid": False,
                "blocker": "certification_claimed_not_false",
                "wallet_db_used": False,
            }

        # Tamper: recompute body hash
        body = {k: v for k, v in package.items() if k != "hashes"}
        expected = (package.get("hashes") or {}).get("package_body_sha256")
        actual = _sha(body)
        tampered = expected is not None and expected != actual

        cred_results = []
        overall_valid = True
        for cred in package.get("credentials") or []:
            # Signature check independent of Wallet DB
            offline = verify_credential(cred, status_lookup=None)
            sig_ok = bool(offline.get("verified"))
            status_info = self._resolve_status(cred, package)
            revoked = status_info.get("status") == "revoked"
            stale = status_info.get("freshness") == "stale"
            entry = {
                "credential_id": cred.get("credential_id"),
                "signature_verified": sig_ok,
                "status": status_info.get("status"),
                "freshness": status_info.get("freshness"),
                "revoked": revoked,
                "valid": bool(sig_ok and not revoked and not tampered),
                "evidence": cred.get("evidence"),
                "issuer_id": cred.get("issuer_id"),
                "certification_claimed": False,
            }
            if not entry["valid"]:
                overall_valid = False
            cred_results.append(entry)
            # Cache status for offline later
            cache_path = self.cache_dir / f"{str(cred.get('credential_id')).replace(':', '_')}.status.json"
            cache_path.write_text(json.dumps(status_info, indent=2) + "\n")

        # Artifact hash presence (integrity metadata)
        artifact_ok = True
        for art in package.get("artifacts") or []:
            if art.get("certification_claimed") is True:
                artifact_ok = False
                overall_valid = False

        if tampered:
            overall_valid = False

        result = {
            "ok": True,
            "valid": overall_valid and not tampered and artifact_ok,
            "tampered": tampered,
            "credentials": cred_results,
            "artifact_integrity_ok": artifact_ok,
            "privacy_manifest": package.get("privacy_manifest"),
            "wallet_db_used": False,
            "wallet_db_refusal": refuse,
            "status_online": self._status_online,
            "verified_at": _now(),
            "certification_claimed": False,
        }
        return result

    def _resolve_status(self, cred: Dict[str, Any], package: Dict[str, Any]) -> Dict[str, Any]:
        cid = cred.get("credential_id")
        snap = (package.get("status_snapshot") or {}).get(cid) or {}
        if self._status_online and self._status_provider is not None:
            live = self._status_provider.get(cid) or snap
            return {
                "credential_id": cid,
                "status": live.get("status") or cred.get("status") or "active",
                "updated_at": live.get("updated_at") or _now(),
                "freshness": "fresh",
                "certification_claimed": False,
            }
        # Offline: use cache or package snapshot — label stale honestly
        cache_path = self.cache_dir / f"{str(cid).replace(':', '_')}.status.json"
        if cache_path.is_file():
            cached = json.loads(cache_path.read_text())
            cached["freshness"] = "stale"
            cached["certification_claimed"] = False
            return cached
        out = dict(snap) if snap else {
            "credential_id": cid,
            "status": cred.get("status") or "active",
            "updated_at": package.get("status_snapshot_at") or package.get("created_at"),
        }
        out["freshness"] = "stale"
        out["certification_claimed"] = False
        return out

    def verify_tampered_copy(self, package: Dict[str, Any]) -> Dict[str, Any]:
        bad = copy.deepcopy(package)
        # Mutate a credential name without updating hashes
        if bad.get("credentials"):
            bad["credentials"][0]["name"] = (bad["credentials"][0].get("name") or "") + "-TAMPERED"
        return self.verify_package(bad)
