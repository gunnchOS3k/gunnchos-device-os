"""CX3.3 host provider journeys — education/career digital closure GUI APIs."""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.request import Request, urlopen

from gunnchos_device_os.cx3_3.paths import (
    career_data_root,
    career_package_root,
    education_data_root,
    ensure_lab_tree,
    portfolio_data_root,
    share_data_root,
    skill_graph_root,
    verifier_cache_root,
    wallet_data_root,
)

PROVIDER_PORT = 8773


def _http_json(method: str, url: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except Exception as exc:  # noqa: BLE001
        body = ""
        try:
            body = exc.read().decode("utf-8")  # type: ignore[attr-defined]
        except Exception:
            body = str(exc)
        try:
            parsed = json.loads(body) if body.startswith("{") else {"raw": body}
        except Exception:
            parsed = {"raw": body}
        return {"ok": False, "blocker": type(exc).__name__, "detail": parsed}


def start_host_provider(repo: Path) -> Dict[str, Any]:
    lab = ensure_lab_tree(repo)
    script = lab / "scripts" / "cx3_3_provider.py"
    if not script.is_file():
        return {"ok": False, "blocker": "CX33_PROVIDER_SCRIPT_MISSING"}
    env = os.environ.copy()
    env["CX33_REPO"] = str(repo)
    env["CX33_ROOT"] = str(lab / "work" / "provider_root")
    env["CX33_WALLET_ROOT"] = str(wallet_data_root(repo))
    env["CX33_PORTFOLIO_ROOT"] = str(portfolio_data_root(repo))
    env["CX33_CAREER_ROOT"] = str(career_data_root(repo))
    env["CX33_SHARE_ROOT"] = str(share_data_root(repo))
    env["CX33_EDUCATION_ROOT"] = str(education_data_root(repo))
    env["CX33_SKILL_GRAPH_ROOT"] = str(skill_graph_root(repo))
    env["CX33_CAREER_PACKAGE_ROOT"] = str(career_package_root(repo))
    env["CX33_VERIFIER_CACHE"] = str(verifier_cache_root(repo))
    env["CX33_BIND"] = "127.0.0.1"
    env["CX33_PORT"] = str(PROVIDER_PORT)
    env["PYTHONPATH"] = str(repo) + os.pathsep + env.get("PYTHONPATH", "")
    Path(env["CX33_ROOT"]).mkdir(parents=True, exist_ok=True)
    log_path = lab / "work" / "provider.log"
    logf = open(log_path, "w")
    candidates = [
        Path(os.environ.get("CX33_PYTHON") or ""),
        repo / ".venv" / "bin" / "python",
        repo.parent / "cx3-waike-career-sharing-verifier" / ".venv" / "bin" / "python",
        repo.parent / "cx3-credential-wallet" / ".venv" / "bin" / "python",
        Path("/Users/gunnchos/Downloads/gunnchos-7gc-research-product-spine/repos/gunnchos-device-os/.worktrees/cx3-waike-career-sharing-verifier/.venv/bin/python"),
    ]
    python = "python3"
    for cand in candidates:
        if cand and cand.is_file():
            python = str(cand)
            break
    proc = subprocess.Popen([python, str(script)], cwd=str(repo), env=env, stdout=logf, stderr=subprocess.STDOUT)
    base = f"http://127.0.0.1:{PROVIDER_PORT}"
    for _ in range(50):
        try:
            health = _http_json("GET", f"{base}/api/health")
            if health.get("ok"):
                return {
                    "ok": True,
                    "pid": proc.pid,
                    "base": base,
                    "log": str(log_path),
                    "python": python,
                    "certification_claimed": False,
                }
        except Exception:
            pass
        time.sleep(0.2)
    try:
        proc.terminate()
    except Exception:
        pass
    return {"ok": False, "blocker": "CX33_PROVIDER_START_TIMEOUT", "log": str(log_path)}


def stop_host_provider(info: Optional[Dict[str, Any]]) -> None:
    if not info or not info.get("pid"):
        return
    try:
        os.kill(int(info["pid"]), 15)
    except Exception:
        pass


def run_digital_closure_gui_journey(repo: Path, provider: Dict[str, Any]) -> Dict[str, Any]:
    if not provider.get("ok"):
        return {
            "ok": False,
            "blocker": "provider_down",
            "CX3_NO_SECOND_COMPUTER_FINAL_PASS": False,
        }
    base = provider["base"]
    out: Dict[str, Any] = {"certification_claimed": False}
    try:
        health = _http_json("GET", f"{base}/api/health")
        edu_j = _http_json("POST", f"{base}/api/journey/education_timeline", {})
        skill_j = _http_json("POST", f"{base}/api/journey/skill_graph", {})
        career_j = _http_json("POST", f"{base}/api/journey/career_profile", {})
        pkg_j = _http_json("POST", f"{base}/api/journey/career_package", {})
        recover_j = _http_json(
            "POST", f"{base}/api/journey/recovery", {"package_dir": pkg_j.get("package_dir")}
        )
        verify_j = _http_json("POST", f"{base}/api/journey/verifier", {})
        surfaces = all(
            (repo / "apps" / "gunnch_shell" / "src" / "surfaces" / name).is_file()
            for name in (
                "CareerProfileSurface.tsx",
                "VerifierSurface.tsx",
                "WalletSurface.tsx",
                "PortfolioSurface.tsx",
                "EducationTimelineSurface.tsx",
                "SkillEvidenceGraphSurface.tsx",
            )
        )
        no_second = (
            health.get("ok")
            and edu_j.get("ok")
            and skill_j.get("ok")
            and career_j.get("ok")
            and pkg_j.get("ok")
            and recover_j.get("ok")
            and verify_j.get("ok")
            and verify_j.get("wallet_db_used") is False
            and surfaces
            and edu_j.get("certification_claimed") is False
        )
        out.update(
            {
                "ok": no_second,
                "health": health,
                "education": edu_j,
                "skill_graph": skill_j,
                "career": career_j,
                "career_package": pkg_j,
                "recovery": recover_j,
                "verifier": verify_j,
                "surfaces_present": surfaces,
                "CX3_NO_SECOND_COMPUTER_FINAL_PASS": no_second,
            }
        )
        return out
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "blocker": type(exc).__name__,
            "detail": str(exc),
            "CX3_NO_SECOND_COMPUTER_FINAL_PASS": False,
            "certification_claimed": False,
        }
