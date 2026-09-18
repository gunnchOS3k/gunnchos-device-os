"""CX3.2 host provider journeys — Career Profile + Verifier GUI APIs."""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.request import Request, urlopen

from gunnchos_device_os.cx3_2.paths import (
    career_data_root,
    ensure_lab_tree,
    portfolio_data_root,
    share_data_root,
    verifier_cache_root,
    wallet_data_root,
)

PROVIDER_PORT = 8772


def _http_json(method: str, url: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = Request(url, data=data, headers=headers, method=method)
    with urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body) if body else {}


def start_host_provider(repo: Path) -> Dict[str, Any]:
    lab = ensure_lab_tree(repo)
    script = lab / "scripts" / "cx3_2_provider.py"
    if not script.is_file():
        return {"ok": False, "blocker": "CX32_PROVIDER_SCRIPT_MISSING"}
    env = os.environ.copy()
    env["CX32_REPO"] = str(repo)
    env["CX32_ROOT"] = str(lab / "work" / "provider_root")
    env["CX32_WALLET_ROOT"] = str(wallet_data_root(repo))
    env["CX32_PORTFOLIO_ROOT"] = str(portfolio_data_root(repo))
    env["CX32_CAREER_ROOT"] = str(career_data_root(repo))
    env["CX32_SHARE_ROOT"] = str(share_data_root(repo))
    env["CX32_VERIFIER_CACHE"] = str(verifier_cache_root(repo))
    env["CX32_BIND"] = "127.0.0.1"
    env["CX32_PORT"] = str(PROVIDER_PORT)
    env["PYTHONPATH"] = str(repo) + os.pathsep + env.get("PYTHONPATH", "")
    Path(env["CX32_ROOT"]).mkdir(parents=True, exist_ok=True)
    log_path = lab / "work" / "provider.log"
    logf = open(log_path, "w")
    py = repo / ".venv" / "bin" / "python"
    python = str(py) if py.is_file() else "python3"
    proc = subprocess.Popen([python, str(script)], cwd=str(repo), env=env, stdout=logf, stderr=subprocess.STDOUT)
    base = f"http://127.0.0.1:{PROVIDER_PORT}"
    for _ in range(50):
        try:
            health = _http_json("GET", f"{base}/api/health")
            if health.get("ok"):
                return {"ok": True, "pid": proc.pid, "base": base, "log": str(log_path), "certification_claimed": False}
        except Exception:
            time.sleep(0.2)
    try:
        proc.terminate()
    except Exception:
        pass
    return {"ok": False, "blocker": "CX32_PROVIDER_START_TIMEOUT", "log": str(log_path)}


def stop_host_provider(info: Optional[Dict[str, Any]]) -> None:
    if not info or not info.get("pid"):
        return
    try:
        os.kill(int(info["pid"]), 15)
    except Exception:
        pass


def run_career_verifier_gui_journey(repo: Path, provider: Dict[str, Any]) -> Dict[str, Any]:
    if not provider.get("ok"):
        return {
            "ok": False,
            "blocker": "provider_down",
            "CX3_REAL_CAREER_PROFILE_GUI_PASS": False,
            "CX3_REAL_VERIFIER_GUI_PASS": False,
            "CX3_NO_SECOND_COMPUTER_CAREER_PASS": False,
        }
    base = provider["base"]
    out: Dict[str, Any] = {"certification_claimed": False}
    try:
        health = _http_json("GET", f"{base}/api/health")
        career_j = _http_json("POST", f"{base}/api/journey/career_profile", {})
        resume_j = _http_json("POST", f"{base}/api/career/resume_export", {"include_fields": [
            "display_name", "headline", "summary", "skills", "projects", "credential_refs", "artifact_refs"
        ]})
        share_j = _http_json("POST", f"{base}/api/journey/share_package", {
            "exclude_contact": True,
            "exclude_one_credential": True,
            "exclude_one_artifact": True,
        })
        verify_j = _http_json("POST", f"{base}/api/journey/verifier", {"package_dir": share_j.get("package_dir")})
        shell_career = repo / "apps" / "gunnch_shell" / "src" / "surfaces" / "CareerProfileSurface.tsx"
        shell_ver = repo / "apps" / "gunnch_shell" / "src" / "surfaces" / "VerifierSurface.tsx"
        surfaces = shell_career.is_file() and shell_ver.is_file()
        career_gui = (
            health.get("ok")
            and career_j.get("ok")
            and career_j.get("certification_claimed") is False
            and surfaces
        )
        verifier_gui = (
            bool(verify_j.get("ok"))
            and verify_j.get("wallet_db_used") is False
            and surfaces
        )
        no_second = career_gui and bool(resume_j.get("ok")) and bool(share_j.get("ok")) and verifier_gui
        out.update(
            {
                "ok": career_gui and verifier_gui and no_second,
                "health": health,
                "career_journey": career_j,
                "resume": {k: resume_j.get(k) for k in ("ok", "export_sha256", "certification_claimed")},
                "share": {k: share_j.get(k) for k in ("ok", "package_id", "certification_claimed")},
                "verifier": verify_j,
                "shell_surfaces_present": surfaces,
                "CX3_REAL_CAREER_PROFILE_GUI_PASS": career_gui,
                "CX3_REAL_VERIFIER_GUI_PASS": verifier_gui,
                "CX3_NO_SECOND_COMPUTER_CAREER_PASS": no_second,
            }
        )
        return out
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "blocker": f"GUI_JOURNEY:{type(exc).__name__}",
            "detail": str(exc),
            "CX3_REAL_CAREER_PROFILE_GUI_PASS": False,
            "CX3_REAL_VERIFIER_GUI_PASS": False,
            "CX3_NO_SECOND_COMPUTER_CAREER_PASS": False,
        }
